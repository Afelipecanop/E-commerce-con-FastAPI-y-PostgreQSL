from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine
from dotenv import load_dotenv
import os

load_dotenv()

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

@app.get("/")
def root():
    return {"mensaje": "API funcionando ✅"}

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0"
    }


@app.get("/db-check")
def db_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "conectada ✅"}
    except Exception as e:
        return {"database": "error ❌", "detalle": str(e)}
    
