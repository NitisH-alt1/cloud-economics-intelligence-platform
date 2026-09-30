import os

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if APP_ENV == "production" and not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY must be set when APP_ENV=production.")
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = "development-only-change-this-secret"

JWT_ALGORITHM = "HS256"

JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)
