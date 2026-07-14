import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # set ENVIRONMENT=production in Render


def _get_secret_key() -> str:
    key = os.getenv("SECRET_KEY", "")
    if not key:
        if ENVIRONMENT == "production":
            # Fail loudly instead of silently running with an insecure default —
            # this is the whole point of catching it here rather than at request time.
            sys.exit("FATAL: SECRET_KEY environment variable is not set in production.")
        return "dev-secret-change-this"  # fine for local dev only
    return key


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        # Local dev fallback — make sure the instance/ folder actually exists,
        # since SQLite won't create parent directories itself.
        instance_dir = os.path.join(BASE_DIR, "instance")
        os.makedirs(instance_dir, exist_ok=True)
        return f"sqlite:///{os.path.join(instance_dir, 'alzheimer.db')}"

    # Render/Railway both give Postgres URLs with the old "postgres://" scheme;
    # SQLAlchemy 1.4+/2.0 requires "postgresql://".
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Settings:
    SECRET_KEY: str = _get_secret_key()
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DATABASE_URL: str = _get_database_url()
    MODEL_PATH: str = os.getenv("MODEL_PATH", os.path.join(BASE_DIR, "ml_model", "densenet_model.h5"))

    def __init__(self):
        # Catch missing pieces at startup, not mid-request — much easier to debug
        # from Render's deploy logs than from a random 500 error later.
        if ENVIRONMENT == "production" and not self.GEMINI_API_KEY:
            print("⚠️  WARNING: GEMINI_API_KEY not set — AI summaries will use fallback text only.")
        if not os.path.exists(self.MODEL_PATH):
            print(f"⚠️  WARNING: Model file not found at {self.MODEL_PATH} — predictions will fail.")


settings = Settings()