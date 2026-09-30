"""SQLite identity store, versioned schema, append-only audit and offline recovery."""
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time

from .settings import Settings

ROLE_CAPABILITIES = {
    "root": ["setup:write", "config:write", "users:write", "audit:read", "backups:write", "models:write", "models:read", "data:write", "data:read"],
    "sysadmin": ["config:write", "backups:write", "models:read"],
    "secopsadmin": ["users:write", "audit:read", "models:read"],
    "mlopsadmin": ["models:read", "models:write", "data:write", "data:read"],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL COLLATE NOCASE, password_hash TEXT NOT NULL, must_change_password INTEGER NOT NULL DEFAULT 1, active INTEGER NOT NULL DEFAULT 1, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS roles(name TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS capabilities(name TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS role_capabilities(role TEXT REFERENCES roles(name), capability TEXT REFERENCES capabilities(name), PRIMARY KEY(role,capability));
CREATE TABLE IF NOT EXISTS user_roles(user_id TEXT REFERENCES users(id), role TEXT REFERENCES roles(name), PRIMARY KEY(user_id,role));
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id), csrf_token TEXT NOT NULL, expires_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS instance_config(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS auth_attempts(subject_hash TEXT PRIMARY KEY, attempts INTEGER NOT NULL, window_start REAL NOT NULL);
CREATE TABLE IF NOT EXISTS audit_events(id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id TEXT, action TEXT NOT NULL, payload TEXT NOT NULL, created_at REAL NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_events BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_events BEGIN SELECT RAISE(ABORT, 'audit is append-only'); END;
CREATE VIEW IF NOT EXISTS effective_capabilities AS SELECT DISTINCT ur.user_id, rc.capability FROM user_roles ur JOIN role_capabilities rc ON ur.role=rc.role;
CREATE TABLE IF NOT EXISTS backups(id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, sha256 TEXT NOT NULL, created_at REAL NOT NULL);
"""


def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def check_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def validate_password(password: str):
    if not 15 <= len(password) <= 128:
        raise ValueError("La contraseña debe tener entre 15 y 128 caracteres.")
    if len(set(password)) < 5:
        raise ValueError("Utiliza una frase de contraseña menos repetitiva.")


class Store:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.path = settings.state_dir / "framework.sqlite3"

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self):
        self.settings.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != "nt":
            os.chmod(self.settings.state_dir, 0o700)
        digest = hashlib.sha256(SCHEMA.encode()).hexdigest()
        credentials_path = self.settings.state_dir / "bootstrap-credentials.json"
        with self.connect() as db:
            db.executescript(SCHEMA)
            db.execute("BEGIN IMMEDIATE")
            migration = db.execute("SELECT checksum FROM schema_migrations WHERE version=1").fetchone()
            if migration and migration[0] != digest:
                raise RuntimeError("Schema migration checksum mismatch")
            db.execute("INSERT OR IGNORE INTO schema_migrations VALUES(1,?,?)", (digest,time.time()))
            for role, caps in ROLE_CAPABILITIES.items():
                db.execute("INSERT OR IGNORE INTO roles VALUES(?)", (role,))
                for cap in caps:
                    db.execute("INSERT OR IGNORE INTO capabilities VALUES(?)", (cap,))
                    db.execute("INSERT OR IGNORE INTO role_capabilities VALUES(?,?)", (role,cap))
            if self.settings.mode == "framework" and not db.execute("SELECT 1 FROM users").fetchone():
                password = secrets.token_urlsafe(24)
                user_id = self.create_user(db, "root", password, "root")
                descriptor = os.open(credentials_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    json.dump({"username":"root", "password":password, "purpose":"First access only; mandatory password change"}, handle)
                self.audit(db, user_id, "bootstrap.created", {})
        return credentials_path if credentials_path.exists() else None

    def create_user(self, db, username, password, role):
        user_id = secrets.token_hex(16)
        db.execute("INSERT INTO users VALUES(?,?,?,?,?,?)", (user_id,username,password_hash(password),1,1,time.time()))
        db.execute("INSERT INTO user_roles VALUES(?,?)", (user_id,role))
        return user_id

    def audit(self, db, actor, action, payload):
        previous = db.execute("SELECT event_hash FROM audit_events ORDER BY id DESC LIMIT 1").fetchone()
        previous_hash = previous[0] if previous else "0" * 64
        timestamp = time.time()
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        material = json.dumps([actor,action,serialized,timestamp,previous_hash], separators=(",", ":"))
        digest = hashlib.sha256(material.encode()).hexdigest()
        db.execute("INSERT INTO audit_events(actor_id,action,payload,created_at,previous_hash,event_hash) VALUES(?,?,?,?,?,?)", (actor,action,serialized,timestamp,previous_hash,digest))

    def user(self, db, user_id):
        row = db.execute("SELECT id,username,must_change_password FROM users WHERE id=? AND active=1", (user_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result["must_change_password"] = bool(result["must_change_password"])
        result["roles"] = [r[0] for r in db.execute("SELECT role FROM user_roles WHERE user_id=?", (user_id,))]
        result["capabilities"] = [r[0] for r in db.execute("SELECT capability FROM effective_capabilities WHERE user_id=?", (user_id,))]
        return result

    def setup_required(self, db):
        return db.execute("SELECT value FROM instance_config WHERE key='setup_complete'").fetchone() is None

    def backup(self, actor=None):
        directory = self.settings.state_dir / "backups"
        directory.mkdir(exist_ok=True, mode=0o700)
        name = f"framework-{time.time_ns()}.sqlite3"
        target = directory / name
        with self.connect() as source:
            destination = sqlite3.connect(target)
            try:
                source.backup(destination)
                if destination.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Backup integrity check failed")
            finally:
                destination.close()
        if os.name != "nt":
            os.chmod(target, 0o600)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest = {"name":name,"sha256":digest,"created_at":time.time()}
        with self.connect() as db:
            db.execute("INSERT INTO backups VALUES(?,?,?,?)", (secrets.token_hex(16),name,digest,manifest["created_at"]))
            self.audit(db,actor,"backup.created",manifest)
        return manifest

    @staticmethod
    def restore_backup(source: Path, destination: Path, expected_sha256: str):
        source, destination = Path(source).resolve(), Path(destination).resolve()
        # Reuse the protected-path invariant before any write.
        Settings(state_dir=destination.parent)
        if destination.exists():
            raise ValueError("Restore requires a new destination; existing databases are never overwritten")
        if not hmac.compare_digest(hashlib.sha256(source.read_bytes()).hexdigest(), expected_sha256):
            raise ValueError("Backup checksum mismatch")
        original = sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)
        try:
            if original.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Invalid backup")
            if not original.execute("SELECT 1 FROM schema_migrations WHERE version=1").fetchone():
                raise ValueError("Unknown database schema")
            destination.parent.mkdir(parents=True, exist_ok=True)
            restored = sqlite3.connect(destination)
            try:
                original.backup(restored)
                restored.execute("DELETE FROM sessions")
                restored.commit()
            finally:
                restored.close()
        finally:
            original.close()
        return destination
