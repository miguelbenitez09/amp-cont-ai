"""Canonical public HTTP entrypoint. No imports from the legacy control plane."""
from contextlib import asynccontextmanager
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sqlite3
import time

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .settings import Settings
from .store import Store, check_password, password_hash, validate_password
from .ml import ModelService, RECIPES


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1,max_length=128)
    new_password: str = Field(min_length=15,max_length=128)


class Administrator(BaseModel):
    username: str = Field(min_length=3,max_length=80,pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=15,max_length=128)
    role: str


class Setup(BaseModel):
    admins: list[Administrator] = Field(min_length=3,max_length=3)


class Configuration(BaseModel):
    display_name: str = Field(min_length=1,max_length=100)
    description: str = Field(default="",max_length=1000)

class DatasetImport(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    csv_text: str = Field(min_length=1, max_length=2_000_000)
    date_column: str = Field(min_length=1, max_length=80)
    target_column: str = Field(min_length=1, max_length=80)
    feature_columns: list[str] = Field(default_factory=list, max_length=12)

class TrainingRequest(BaseModel):
    dataset_id: str
    recipe_id: str


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    store = Store(settings)
    model_service = ModelService(settings.state_dir / "framework.sqlite3", settings.state_dir)

    @asynccontextmanager
    async def lifespan(app):
        store.initialize()
        model_service.initialize()
        yield

    app = FastAPI(title="AMP-CONT-AI Framework",version=__version__,lifespan=lifespan)
    app.state.store = store
    app.state.settings = settings

    @app.middleware("http")
    async def security_headers(request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            expected = str(request.base_url).rstrip("/")
            if origin and origin.rstrip("/") != expected:
                return Response("Origen no permitido", status_code=403, media_type="text/plain")
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
        if settings.secure_cookies:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def require_framework():
        if settings.mode != "framework":
            raise HTTPException(409,"La instancia está en modo portal. Activa AMP_MODE=framework mediante el instalador.")

    def authenticated(request: Request, capability=None, allow_rotation=False):
        require_framework()
        token = request.cookies.get("amp_session", "")
        digest = hashlib.sha256(token.encode()).hexdigest()
        with store.connect() as db:
            session = db.execute("SELECT * FROM sessions WHERE token_hash=? AND expires_at>?", (digest,time.time())).fetchone()
            user = store.user(db, session["user_id"]) if session else None
        if not user:
            raise HTTPException(401,"Inicia sesión para continuar.")
        if request.method not in {"GET","HEAD","OPTIONS"} and not hmac.compare_digest(request.headers.get("X-CSRF-Token", ""),session["csrf_token"]):
            raise HTTPException(403,"La sesión requiere un token CSRF válido. Vuelve a cargar la página.")
        if user["must_change_password"] and not allow_rotation:
            raise HTTPException(403,"Debes cambiar la contraseña temporal antes de continuar.")
        if capability and capability not in user["capabilities"]:
            raise HTTPException(403,"Tu rol no permite esta operación.")
        return user, session["csrf_token"]

    # Other canonical modules share this authorization boundary.
    app.state.authenticate = authenticated

    def session_response(db, response, user_id):
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        db.execute("INSERT INTO sessions VALUES(?,?,?,?)", (hashlib.sha256(token.encode()).hexdigest(),user_id,csrf,time.time()+settings.session_hours*3600))
        response.set_cookie("amp_session",token,httponly=True,secure=settings.secure_cookies,samesite="strict",max_age=settings.session_hours*3600,path="/")
        return {"user":store.user(db,user_id),"csrf_token":csrf}

    @app.get("/api/status")
    def status():
        with store.connect() as db:
            setup_required = store.setup_required(db)
            db.execute("SELECT 1")
        return {"mode":settings.mode,"version":__version__,"setup_required":setup_required,
                "bootstrap_available":settings.mode == "framework" and setup_required,
                "capabilities":["identity","configuration","audit","backups","datasets","models","training"] if settings.mode == "framework" else [],
                "roles":["root","sysadmin","secopsadmin","mlopsadmin"] if settings.mode == "framework" else [],
                "services":[{"name":"database","status":"ready"}],
                "security":{"transport":"https-local" if settings.secure_cookies else "http-loopback-only","secure_cookies":settings.secure_cookies,"csrf":"required-for-state-changing-requests","csp":"enabled"},
                "message":"Portal educativo" if settings.mode == "portal" else "Instancia local"}

    @app.get("/health")
    def health():
        with store.connect() as db:
            db.execute("SELECT 1")
        return {"status":"ok","version":__version__}

    @app.post("/api/auth/login")
    def login(body: Login, request: Request, response: Response):
        require_framework()
        subject = hashlib.sha256(f"{request.client.host if request.client else 'local'}:{body.username.casefold()}".encode()).hexdigest()
        failure = False
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            attempt = db.execute("SELECT * FROM auth_attempts WHERE subject_hash=?", (subject,)).fetchone()
            if attempt and attempt["window_start"] > time.time()-900 and attempt["attempts"] >= 10:
                raise HTTPException(429,"Demasiados intentos. Espera 15 minutos.")
            row = db.execute("SELECT * FROM users WHERE username=? AND active=1", (body.username,)).fetchone()
            if not row or not check_password(body.password,row["password_hash"]):
                count = attempt["attempts"]+1 if attempt and attempt["window_start"] > time.time()-900 else 1
                window = attempt["window_start"] if count > 1 else time.time()
                db.execute("INSERT OR REPLACE INTO auth_attempts VALUES(?,?,?)", (subject,count,window))
                failure = True
            else:
                db.execute("DELETE FROM auth_attempts WHERE subject_hash=?", (subject,))
                result = session_response(db,response,row["id"])
                store.audit(db,row["id"],"session.created",{})
        if failure:
            raise HTTPException(401,"Usuario o contraseña incorrectos.")
        return result

    @app.get("/api/auth/me")
    def me(request: Request):
        user, csrf = authenticated(request,allow_rotation=True)
        return {"user":user,"csrf_token":csrf}

    @app.post("/api/auth/password")
    def change_password(body: PasswordChange, request: Request, response: Response):
        user, _ = authenticated(request,allow_rotation=True)
        try:
            validate_password(body.new_password)
        except ValueError as error:
            raise HTTPException(422,str(error)) from error
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()
            if not check_password(body.current_password,row[0]):
                raise HTTPException(400,"La contraseña actual es incorrecta.")
            if check_password(body.new_password,row[0]):
                raise HTTPException(422,"La contraseña nueva debe ser diferente.")
            db.execute("UPDATE users SET password_hash=?,must_change_password=0 WHERE id=?", (password_hash(body.new_password),user["id"]))
            db.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
            store.audit(db,user["id"],"password.changed",{})
            result = session_response(db,response,user["id"])
        if "root" in user["roles"]:
            (settings.state_dir / "bootstrap-credentials.json").unlink(missing_ok=True)
        return result

    @app.post("/api/auth/logout")
    def logout(request: Request,response: Response):
        user, _ = authenticated(request,allow_rotation=True)
        with store.connect() as db:
            digest = hashlib.sha256(request.cookies.get("amp_session", "").encode()).hexdigest()
            db.execute("DELETE FROM sessions WHERE token_hash=?", (digest,))
            store.audit(db,user["id"],"session.closed",{})
        response.delete_cookie("amp_session",path="/")
        return {"message":"Sesión cerrada."}

    @app.post("/api/setup/admins")
    def setup_admins(body: Setup,request: Request):
        user,_ = authenticated(request,"setup:write")
        if {a.role for a in body.admins} != {"sysadmin","secopsadmin","mlopsadmin"}:
            raise HTTPException(422,"Debes asignar una cuenta a cada rol administrativo.")
        if len({a.username.casefold() for a in body.admins}) != 3:
            raise HTTPException(422,"Los nombres de usuario deben ser diferentes.")
        for admin in body.admins:
            try:
                validate_password(admin.password)
            except ValueError as error:
                raise HTTPException(422,str(error)) from error
        created = [{"username":a.username,"role":a.role} for a in body.admins]
        try:
            with store.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                if not store.setup_required(db):
                    raise HTTPException(409,"La configuración inicial ya está completada.")
                for admin in body.admins:
                    store.create_user(db,admin.username,admin.password,admin.role)
                db.execute("INSERT INTO instance_config VALUES('setup_complete','true')")
                store.audit(db,user["id"],"setup.completed",{"created":created})
        except sqlite3.IntegrityError as error:
            raise HTTPException(409,"Un nombre de usuario ya existe. No se creó ninguna cuenta.") from error
        return {"created":created,"setup_complete":True,"password_changes_required":3}

    @app.get("/api/config")
    def get_config(request: Request):
        authenticated(request,"config:write")
        with store.connect() as db:
            values = {r["key"]:r["value"] for r in db.execute("SELECT key,value FROM instance_config WHERE key IN ('display_name','description')")}
        values.setdefault("display_name","AMP-CONT-AI")
        values.setdefault("description","")
        return {"values":values,"editable":["display_name","description"],"restart_required":[],
                "environment":{"AMP_MODE":settings.mode,"AMP_SECURE_COOKIES":settings.secure_cookies,"AMP_SESSION_HOURS":settings.session_hours}}

    @app.put("/api/config")
    def update_config(body: Configuration,request: Request):
        user,_ = authenticated(request,"config:write")
        with store.connect() as db:
            for key,value in body.model_dump().items():
                db.execute("INSERT OR REPLACE INTO instance_config VALUES(?,?)", (key,value))
            store.audit(db,user["id"],"config.changed",{"keys":list(body.model_dump())})
        return get_config(request)

    @app.get("/api/audit")
    def audit(request: Request):
        authenticated(request,"audit:read")
        with store.connect() as db:
            items = [dict(r) for r in db.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT 100")]
        for item in items:
            item["payload"] = json.loads(item["payload"])
        return {"items":items,"guarantee":"Append-only application audit; SQLite owner can modify database files."}

    @app.get("/api/backups")
    def backups(request: Request):
        authenticated(request,"backups:write")
        with store.connect() as db:
            return {"items":[dict(r) for r in db.execute("SELECT name,sha256,created_at FROM backups ORDER BY created_at DESC")]}

    @app.post("/api/backups")
    def create_backup(request: Request):
        user,_ = authenticated(request,"backups:write")
        return store.backup(user["id"])

    @app.get("/api/models")
    def models():
        return {"items":model_service.models(),"message":"Modelos locales verificables; ningún artefacto se ejecuta sin revisión."}

    @app.get("/api/recipes")
    def recipes():
        return {"items": RECIPES}

    @app.post("/api/datasets")
    def import_dataset(body: DatasetImport, request: Request):
        user, _ = authenticated(request, "data:write")
        try:
            item = model_service.import_csv(body.name, body.csv_text, body.date_column, body.target_column, body.feature_columns)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        with store.connect() as db:
            store.audit(db, user["id"], "dataset.imported", {"dataset_id": item["id"], "sha256": item["content_sha256"]})
        return item

    @app.get("/api/datasets")
    def datasets(request: Request):
        authenticated(request, "data:read")
        return {"items": model_service.datasets()}

    @app.post("/api/datasets/{dataset_id}/review")
    def review_dataset(dataset_id: str, request: Request):
        user, _ = authenticated(request, "data:write")
        try:
            item = model_service.review(dataset_id, user["id"])
        except ValueError as error:
            raise HTTPException(404, str(error)) from error
        with store.connect() as db:
            store.audit(db, user["id"], "dataset.reviewed", {"dataset_id": dataset_id})
        return item

    @app.post("/api/training")
    def train(body: TrainingRequest, request: Request):
        user, _ = authenticated(request, "models:write")
        try:
            result = model_service.train(body.dataset_id, body.recipe_id, user["id"])
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        with store.connect() as db:
            store.audit(db, user["id"], "model.trained", {"model_id": result["model_id"], "run_id": result["id"]})
        return result

    @app.get("/api/models/{model_id}")
    def model_detail(model_id: str, request: Request):
        authenticated(request, "models:read")
        try:
            return model_service.artifact(model_id)
        except ValueError as error:
            raise HTTPException(404, str(error)) from error

    @app.post("/api/models/{model_id}/predict")
    def predict(model_id: str, payload: dict, request: Request):
        authenticated(request, "models:read")
        try:
            return model_service.predict(model_id, payload)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @app.get("/api/agents")
    def agents(request: Request):
        authenticated(request)
        return {"items":[],"available":False,"message":"La ejecución de agentes y herramientas MCP todavía no está implementada en esta distribución."}

    @app.get("/api/roles")
    def roles(request: Request):
        authenticated(request, "users:write")
        with store.connect() as db:
            items=[]
            for role in db.execute("SELECT name FROM roles ORDER BY name"):
                capabilities=[row[0] for row in db.execute("SELECT capability FROM role_capabilities WHERE role=? ORDER BY capability",(role[0],))]
                items.append({"name":role[0],"capabilities":capabilities})
        return {"items":items}

    static = Path(__file__).resolve().parents[1] / "serving" / "static" / "framework"
    if static.is_dir():
        app.mount("/static/framework",StaticFiles(directory=static),name="framework-assets")

    @app.get("/",include_in_schema=False)
    def portal():
        landing = static.parent / "landing.html"
        return FileResponse(landing if landing.exists() else static / "index.html",headers={"Cache-Control":"no-cache"})

    @app.get("/app",include_in_schema=False)
    def workspace():
        return FileResponse(static / "app.html",headers={"Cache-Control":"no-cache"})

    return app


app = create_app()
