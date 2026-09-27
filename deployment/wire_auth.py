from pathlib import Path

app_path = Path("dashboard/app.py")
source = app_path.read_text(encoding="utf-8")

if "from auth.router import router as auth_router" not in source:
    source = (
        "from auth.router import router as auth_router\n"
        "from auth.account_router import router as account_router\n"
        "from database.init_db import init_db\n"
        + source
    )

if "auth_router" not in source.split("app = FastAPI", 1)[-1]:
    marker = "app = FastAPI("
    if marker in source:
        insert_at = source.index(marker)
        source = (
            source[:insert_at]
            + "init_db()\n\n"
            + source[insert_at:]
        )

if "app.include_router(auth_router)" not in source:
    source += """

app.include_router(auth_router)
app.include_router(account_router)
"""

app_path.write_text(source, encoding="utf-8")
print("FASTAPI AUTH ROUTES: WIRED")
