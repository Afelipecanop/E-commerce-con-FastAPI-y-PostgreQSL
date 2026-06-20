from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models.cart import Cart, CartItem
from models.product import Product
from schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from middleware.auth import get_current_user

router = APIRouter(prefix="/cart", tags=["Carrito"])


def get_cart_total(cart: Cart) -> float:
    """Calcula el total del carrito sumando precio x cantidad de cada item."""
    return sum(item.product.price * item.quantity for item in cart.items)


@router.get("/", response_model=CartResponse)
def get_cart(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Devuelve el carrito del usuario autenticado con su total."""
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrito no encontrado"
        )
    return CartResponse(
        id=cart.id,
        items=cart.items,
        total=get_cart_total(cart)
    )


@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item_data: CartItemAdd,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agrega un producto al carrito. Si ya existe, suma la cantidad."""

    # Verifica que el producto existe y tiene stock
    product = db.query(Product).filter(
        Product.id == item_data.product_id,
        Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    if product.stock < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Disponible: {product.stock}"
        )

    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()

    # Si el producto ya está en el carrito, suma la cantidad
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item_data.product_id
    ).first()

    if existing_item:
        existing_item.quantity += item_data.quantity
    else:
        new_item = CartItem(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity
        )
        db.add(new_item)

    db.commit()
    return {"mensaje": f"'{product.name}' agregado al carrito ✅"}


@router.put("/items/{item_id}")
def update_cart_item(
    item_id: UUID,
    item_data: CartItemUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza la cantidad de un item en el carrito."""
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado en el carrito"
        )
    if item_data.quantity <= 0:
        db.delete(item)
    else:
        item.quantity = item_data.quantity
    db.commit()
    return {"mensaje": "Carrito actualizado ✅"}


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    item_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina un item del carrito."""
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item no encontrado en el carrito"
        )
    db.delete(item)
    db.commit()