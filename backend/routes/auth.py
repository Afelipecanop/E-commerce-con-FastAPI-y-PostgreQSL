from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db
from models.user import User
from models.cart import Cart
from schemas.user import UserCreate, UserLogin, UserResponse, Token
from services.auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_user_by_email
)
from middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario y crea su carrito automáticamente."""

    # Verifica que el email no esté ya registrado
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email ya está registrado"
        )

    # Crea el usuario con la contraseña hasheada
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(new_user)
    db.flush()  # Obtiene el ID del usuario sin hacer commit aún

    # Crea el carrito vacío automáticamente para el nuevo usuario
    cart = Cart(user_id=new_user.id)
    db.add(cart)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Autentica al usuario y devuelve un token JWT."""

    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Crea el token con el ID del usuario
    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Devuelve los datos del usuario autenticado."""
    return current_user