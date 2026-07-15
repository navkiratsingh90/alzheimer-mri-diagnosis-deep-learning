from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# "check_same_thread" is a SQLite-only argument — psycopg2 (Postgres) doesn't
# accept it and raises a TypeError on connect if passed. This was the second
# crash waiting right after adding psycopg2-binary to requirements.txt.
connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    print("Creating DB session")
    db = SessionLocal()
    try:
        yield db
    finally:
        print("Closing DB session")
        db.close()  