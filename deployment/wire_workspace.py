from pathlib import Path

path = Path("dashboard/app.py")

source = path.read_text(encoding="utf-8")

imports = """
from auth.project_router import router as project_router
from auth.workspace_router import router as workspace_router
"""

if "from auth.project_router import router as project_router" not in source:
    source = imports + source

routes = """
app.include_router(project_router)
app.include_router(workspace_router)
"""

if "app.include_router(project_router)" not in source:
    source += routes

path.write_text(source, encoding="utf-8")

print("PROJECT AND WORKSPACE ROUTES REGISTERED")
