from pydantic import BaseModel
from app.models.user import UserRole

class UserAdminResponse(BaseModel):
    id: int
    username: str
    role: UserRole

class UpdateRoleRequest(BaseModel):
    role: UserRole