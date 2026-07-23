from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


# Lo que el usuario manda para registrarse
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


# Lo que el usuario manda para hacer login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Lo que el frontend manda tras un login con Google Identity Services
class GoogleAuth(BaseModel):
    id_token: str


# Lo que la API devuelve sobre un usuario (nunca incluye la contraseña)
class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_admin: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# El token JWT que se devuelve al hacer login
class Token(BaseModel):
    access_token: str
    token_type: str


# Los datos que viven dentro del token
class TokenData(BaseModel):
    user_id: Optional[str] = None