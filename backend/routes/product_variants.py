from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from models.product import Product
from models.product_variant import ProductVariant
from schemas.product_variant import ProductVariantCreate, ProductVariantUpdate, ProductVariantResponse
from middleware.auth import get_current_admin

router = APIRouter(prefix="/products", tags=["Variantes de producto"])


def _get_product_or_404(product_id: UUID, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return product


@router.get("/{product_id}/variants", response_model=List[ProductVariantResponse])
def get_variants(product_id: UUID, db: Session = Depends(get_db)):
    """Lista las variantes activas de un producto. Público."""
    _get_product_or_404(product_id, db)
    return db.query(ProductVariant).filter(
        ProductVariant.product_id == product_id,
        ProductVariant.is_active == True
    ).all()


@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
def create_variant(
    product_id: UUID,
    data: ProductVariantCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Crea una variante para un producto. Solo administradores."""
    _get_product_or_404(product_id, db)
    variant = ProductVariant(product_id=product_id, **data.model_dump())
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


@router.put("/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
def update_variant(
    product_id: UUID,
    variant_id: UUID,
    data: ProductVariantUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Actualiza una variante. Solo administradores."""
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.product_id == product_id
    ).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variante no encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(variant, field, value)
    db.commit()
    db.refresh(variant)
    return variant


@router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(
    product_id: UUID,
    variant_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Desactiva una variante (no la borra de la DB). Solo administradores."""
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.product_id == product_id
    ).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variante no encontrada")
    variant.is_active = False
    db.commit()
