import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
AUTH_PAGE = BASE_DIR / "pages" / "auth.html"
WORKSPACE_PAGE = BASE_DIR / "pages" / "workspace.html"
ASSETS_DIR = BASE_DIR / "assets"

app = FastAPI(
    title="Cloud Economics Intelligence Platform",
    version="1.0.0",
)

app.mount(
    "/assets",
    StaticFiles(directory=str(ASSETS_DIR)),
    name="assets",
)


@app.get("/")
def home():
    return FileResponse(AUTH_PAGE)


@app.get("/login")
def login():
    return FileResponse(AUTH_PAGE)


@app.get("/signup")
def signup():
    return FileResponse(AUTH_PAGE)


@app.get("/workspace")
def workspace():
    return FileResponse(WORKSPACE_PAGE)


@app.get("/dashboard")
def dashboard():
    return RedirectResponse("/workspace")


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "cloud-economics-public-web",
    }


@app.get("/runtime-config.js", include_in_schema=False)
def runtime_config():
    # The static browser app gets its API origin from the website service's
    # environment. An empty value keeps local development on the same-host:8081
    # default in assets/api.js.
    config = {"apiBaseUrl": os.getenv("API_BASE_URL", "").strip().rstrip("/")}
    return Response(
        f"window.CEA_CONFIG = {json.dumps(config)};",
        media_type="application/javascript",
        headers={"Cache-Control": "no-store"},
    )
