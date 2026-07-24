from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from models.product import Product
from models.product_image import ProductImage
from schemas.product_image import ProductImageCreate, ProductImageUpdate, ProductImageResponse
from middleware.auth import get_current_admin

router = APIRouter(prefix="/products", tags=["Imágenes de producto"])


def _get_product_or_404(product_id: UUID, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return product


def _get_image_or_404(product_id: UUID, image_id: UUID, db: Session) -> ProductImage:
    image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id
    ).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagen no encontrada")
    return image


@router.get("/{product_id}/images", response_model=List[ProductImageResponse])
def get_images(product_id: UUID, db: Session = Depends(get_db)):
    """Lista las imágenes de un producto, en orden. Público."""
    _get_product_or_404(product_id, db)
    return db.query(ProductImage).filter(
        ProductImage.product_id == product_id
    ).order_by(ProductImage.order_index).all()


@router.post("/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
def create_image(
    product_id: UUID,
    data: ProductImageCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Agrega una imagen a la galería del producto. La primera imagen se marca
    automáticamente como principal y sincroniza Product.image_url. Solo administradores."""
    product = _get_product_or_404(product_id, db)
    count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
    is_primary = count == 0
    image = ProductImage(product_id=product_id, url=data.url, order_index=count, is_primary=is_primary)
    db.add(image)
    if is_primary:
        product.image_url = data.url
    db.commit()
    db.refresh(image)
    return image


@router.put("/{product_id}/images/{image_id}", response_model=ProductImageResponse)
def update_image(
    product_id: UUID,
    image_id: UUID,
    data: ProductImageUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Actualiza la URL o el orden de una imagen. Solo administradores."""
    image = _get_image_or_404(product_id, image_id, db)
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(image, field, value)
    if image.is_primary and "url" in updates:
        product = _get_product_or_404(product_id, db)
        product.image_url = image.url
    db.commit()
    db.refresh(image)
    return image


@router.post("/{product_id}/images/{image_id}/set-primary", response_model=ProductImageResponse)
def set_primary_image(
    product_id: UUID,
    image_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Marca una imagen como principal (sincroniza Product.image_url) y desmarca las demás. Solo administradores."""
    image = _get_image_or_404(product_id, image_id, db)
    db.query(ProductImage).filter(ProductImage.product_id == product_id).update({"is_primary": False})
    image.is_primary = True
    product = _get_product_or_404(product_id, db)
    product.image_url = image.url
    db.commit()
    db.refresh(image)
    return image


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    product_id: UUID,
    image_id: UUID,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Borra una imagen de la galería. Solo administradores."""
    image = _get_image_or_404(product_id, image_id, db)
    db.delete(image)
    db.commit()
