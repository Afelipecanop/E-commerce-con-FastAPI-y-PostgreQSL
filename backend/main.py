from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine
from dotenv import load_dotenv
import os

from routes.auth import router as auth_router
from routes.products import router as products_router
from routes.cart import router as cart_router
from routes.payments import router as payments_router

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://e-commerce-con-fastapi-y-postgreqsl-production.up.railway.app",
        os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(
    title="Mi E-commerce API",
    description="Backend de la tienda online",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(payments_router)


@app.get("/")
def root():
    return {"mensaje": "API funcionando ✅"}


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/db-check")
def db_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "conectada ✅"}
    except Exception as e:
        return {"database": "error ❌", "detalle": str(e)}
    
