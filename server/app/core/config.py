import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ----------------------------------------------------
# Project Root
# ----------------------------------------------------
# server/
# ├── .env
# ├── app/
# │   ├── core/
# │   │   └── config.py
# │   └── ml_model/
# │       └── densenet_model.h5
# ----------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR.parent

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


def get_secret_key():
    secret = os.getenv("SECRET_KEY")

    if secret:
        return secret

    if ENVIRONMENT == "production":
        sys.exit("FATAL: SECRET_KEY not configured.")

    return "dev-secret-key"


def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    # Local SQLite
    if not database_url:
        instance = BASE_DIR / "instance"
        instance.mkdir(exist_ok=True)

        return f"sqlite:///{instance / 'alzheimer.db'}"

    # Render compatibility
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    # Render PostgreSQL SSL
    if (
        database_url.startswith("postgresql://")
        and "sslmode=" not in database_url
    ):
        sep = "&" if "?" in database_url else "?"
        database_url += f"{sep}sslmode=require"

    return database_url


class Settings:

    SECRET_KEY = get_secret_key()

    ALGORITHM = os.getenv("ALGORITHM", "HS256")

    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    DATABASE_URL = get_database_url()
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "static/uploads")
    MODEL_PATH = os.getenv(
        "MODEL_PATH",
        str(APP_DIR / "ml_model" / "densenet_model.h5")
    )

    def __init__(self):

        print("=" * 60)
        print("Environment :", ENVIRONMENT)
        print("Database    :", self.DATABASE_URL)
        print("Model Path  :", self.MODEL_PATH)
        print("Model Exists:", os.path.exists(self.MODEL_PATH))
        print("=" * 60) 

        if ENVIRONMENT == "production" and not self.GEMINI_API_KEY:
            print("⚠ GEMINI_API_KEY is not configured.")

        if not os.path.exists(self.MODEL_PATH):
            print("⚠ TensorFlow model file not found.")


settings = Settings()