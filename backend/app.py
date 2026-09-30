"""FastAPI entry point. Run from the project root:  uvicorn backend.app:app --reload"""
import logging
import os
import sqlite3
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from backend.routes import analytics, auth, files, posts, practice, profile, skills, social  # noqa: E402
from backend.utils.config import settings  # noqa: E402
from cloud.database_service import init_db  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")
FRONTEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


@asynccontextmanager
async def lifespan(app):
    settings.SECRET_KEY  # fail fast if not configured
    init_db()
    yield


app = FastAPI(title="Cloud Hobby & Skills Tracker", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

for module in (auth, profile, skills, practice, files, posts, social, analytics):
    app.include_router(module.router)

"""
@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'"
    return resp
"""
@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)

    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"

    # Swagger UI / ReDoc need their own scripts and styles to render.
    if request.url.path not in {"/docs", "/redoc"}:
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline'"
        )

    return resp


@app.exception_handler(sqlite3.Error)
async def db_error(request: Request, exc: sqlite3.Error):
    log.exception("database error on %s", request.url.path)
    return JSONResponse({"detail": "The database is temporarily unavailable. Please try again."}, status_code=503)


@app.exception_handler(Exception)
async def unexpected(request: Request, exc: Exception):
    log.exception("unhandled error on %s", request.url.path)  # details go to logs, not to the user
    return JSONResponse({"detail": "Something went wrong on our side."}, status_code=500)


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(FRONTEND, "index.html"))
