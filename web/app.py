from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
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
    return RedirectResponse("http://127.0.0.1:8081")


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "cloud-economics-public-web",
    }