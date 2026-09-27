from pathlib import Path

path = Path("dashboard/app.py")
source = path.read_text(encoding="utf-8")

import_line = (
    "from auth.cloud_router import router as cloud_router"
)

if import_line not in source:
    source = (
        import_line
        + "\n"
        + source
    )

route_line = "app.include_router(cloud_router)"

if route_line not in source:
    source += "\n" + route_line + "\n"

path.write_text(source, encoding="utf-8")

print("CLOUD ROUTER REGISTERED")
