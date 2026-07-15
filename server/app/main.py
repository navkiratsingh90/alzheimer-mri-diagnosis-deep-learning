from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.core.database import engine, Base
from app.routers import auth, chat, upload, reports, pdf, predictions
from app.core.config import settings
import os
# from app.routers import pdf
app = FastAPI(title="NeuroSight API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://alzheimer-mri-diagnosis-deep-learni-psi.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (uploaded images)
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(reports.router)
app.include_router(predictions.router)
app.include_router(pdf.router)
print(settings.MODEL_PATH) 
print(os.path.exists(settings.MODEL_PATH))

@app.get("/fix-db")
def fix_db():
    # Drop the users table with CASCADE to remove dependent objects
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
        conn.commit()
    
    # Recreate all tables (this will recreate users with the correct schema)
    Base.metadata.create_all(bind=engine)
    return {"message": "✅ Users table recreated with default role"}

@app.get("/")
def root(): 
    return {"message": "NeuroSight API is running"} 

@app.get("/test")
def root(): 
    return {"message": "testing route"} 