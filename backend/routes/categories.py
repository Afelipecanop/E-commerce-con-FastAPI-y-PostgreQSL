from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.category import Category
from models.product import Product
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from schemas.product import ProductResponse
from middleware.auth import get_current_admin

router = APIRouter(prefix="/categories", tags=["Categorías"])

# Categorías por defecto de Velonox
DEFAULT_CATEGORIES = [
    {
        "slug": "ollas",
        "name": "Ollas y cacerolas",
        "description": "Para el sancocho, la sopa y el arroz de cada día.",
        "icon": "ti ti-soup",
        "order_index": 0
    },
    {
        "slug": "sartenes",
        "name": "Sartenes",
        "description": "Desde los huevos del desayuno hasta el pollo del almuerzo.",
        "icon": "ti ti-eggs",
        "order_index": 1
    },
    {
        "slug": "utensilios",
        "name": "Utensilios",
        "description": "Cucharones, espátulas y pinzas para cocinar con precisión.",
        "icon": "ti ti-tools-kitchen-2",
        "order_index": 2
    },
    {
        "slug": "accesorios",
        "name": "Accesorios",
        "description": "Todo lo que complementa tu cocina en acero inoxidable.",
        "icon": "ti ti-slice",
        "order_index": 3
    },
]


@router.get("/", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """Lista todas las categorías activas. Si no hay, inicializa con los defaults."""
    cats = db.query(Category).filter(
        Category.is_active == True
    ).order_by(Category.order_index).all()

    if not cats:
        for cat in DEFAULT_CATEGORIES:
            db.add(Category(**cat))
        db.commit()
        cats = db.query(Category).filter(
            Category.is_active == True
        ).order_by(Category.order_index).all()

    return cats


@router.get("/{slug}", response_model=CategoryResponse)
def get_category(slug: str, db: Session = Depends(get_db)):
    """Devuelve una categoría por su slug."""
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return cat


@router.get("/{slug}/products", response_model=List[ProductResponse])
def get_products_by_category(slug: str, db: Session = Depends(get_db)):
    """Devuelve todos los productos activos de una categoría."""
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    products = db.query(Product).filter(
        Product.category == slug,
        Product.is_active == True
    ).all()

    return products


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Crea una nueva categoría. Solo administradores."""
    existing = db.query(Category).filter(Category.slug == data.slug).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una categoría con ese slug"
        )
    cat = Category(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{slug}", response_model=CategoryResponse)
def update_category(
    slug: str,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Actualiza una categoría. Solo administradores."""
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    slug: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Desactiva una categoría. Solo administradores."""
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    cat.is_active = False
    db.commit()
    