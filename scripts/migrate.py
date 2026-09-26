"""
Database Migration Runner for Panama PortOps-AI v2.0
Executes versioned SQL migrations idempotently.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import sys
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = ROOT_DIR / "db" / "migrations"
DB_PATH = ROOT_DIR / "data" / "enterprise_db" / "portops_platform.db"


def run_migrations(db_path: Path = DB_PATH) -> bool:
    """Executes all migration scripts in numerical order."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Track executed migrations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL
    );
    """)
    conn.commit()

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print(f"No migration files found in {MIGRATIONS_DIR}")
        conn.close()
        return True

    print(f"Applying migrations to {db_path.name}...")
    for mf in migration_files:
        version = mf.stem
        cursor.execute("SELECT 1 FROM schema_migrations WHERE version = ?;", (version,))
        if cursor.fetchone():
            print(f"  [SKIPPED] {version} (already applied)")
            continue

        with open(mf, "r", encoding="utf-8") as f:
            sql_script = f.read()

        try:
            cursor.executescript(sql_script)
            from datetime import datetime, timezone
            cursor.execute("""
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (?, ?);
            """, (version, datetime.now(timezone.utc).isoformat()))
            conn.commit()
            print(f"  [APPLIED] {version}")
        except Exception as e:
            conn.rollback()
            print(f"  [FAILED] {version}: {e}")
            conn.close()
            return False

    conn.close()
    print("All database migrations applied successfully.")
    return True


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
