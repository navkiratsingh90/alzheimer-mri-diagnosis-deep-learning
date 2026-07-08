from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

# Absolute path to the `app/` directory, regardless of where uvicorn is launched from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ^ adjust the number of dirname() calls based on this file's actual location relative to app/
#   if config.py is in app/core/, dirname(dirname(__file__)) == app/

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-this")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./instance/alzheimer.db")
    MODEL_PATH: str = os.getenv("MODEL_PATH", os.path.join(BASE_DIR, "ml_model", "densenet_model.h5"))
    UPLOAD_DIR: str = "static/uploads"

settings = Settings()