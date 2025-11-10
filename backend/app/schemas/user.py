from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Literal, Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Literal["user", "researcher"] = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
