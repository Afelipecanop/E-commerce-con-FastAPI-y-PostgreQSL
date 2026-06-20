from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from models.product import Product
from schemas.product import ProductCreate, ProductUpdate, ProductResponse
from middleware.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/products", tags=["Productos"])


@router.get("/", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    """Lista todos los productos activos. Público — no requiere login."""
    return db.query(Product).filter(Product.is_active == True).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    """Devuelve el detalle de un producto. Público."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)  # Solo admins
):
    """Crea un nuevo producto. Solo administradores."""
    new_product = Product(**product_data.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)  # Solo admins
):
    """Actualiza un producto. Solo administradores."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    for field, value in product_data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)  # Solo admins
):
    """Desactiva un producto (no lo borra de la DB). Solo administradores."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    product.is_active = False
    db.commit()