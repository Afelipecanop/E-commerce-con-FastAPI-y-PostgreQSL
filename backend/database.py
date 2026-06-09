from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Carga las variables del archivo .env
load_dotenv()

# Lee la URL de conexión desde .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Crea el motor de conexión a PostgreSQL
engine = create_engine(DATABASE_URL)

# Cada petición a la API tendrá su propia sesión de DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base de la que heredarán todos tus modelos
Base = declarative_base()


# Función que abre y cierra la sesión automáticamente
# La usarás en cada endpoint que necesite la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()