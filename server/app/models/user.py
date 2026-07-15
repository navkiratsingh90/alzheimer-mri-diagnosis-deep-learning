from sqlalchemy import Column, Integer, String, Enum
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    USER = "USER"      # ✅ uppercase
    ADMIN = "ADMIN"    # ✅ uppercase
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False) 
    role = Column(String, default="user", nullable=False)