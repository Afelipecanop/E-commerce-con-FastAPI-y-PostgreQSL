from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import json
import secrets
import string

from database import get_db
from models.order import Order, OrderItem
from models.product import Product
from models.user import User
from models.cart import Cart, CartItem
from services.auth import hash_password
from services.email import email_bienvenida, email_confirmacion_orden

router = APIRouter(prefix="/guest", tags=["Checkout invitado"])


class CartItemInput(BaseModel):
    product_id: str
    quantity: int


class ShippingAddress(BaseModel):
    direccion: str
    ciudad: str
    departamento: str
    codigo_postal: Optional[str] = None
    telefono: Optional[str] = None
    indicaciones: Optional[str] = None


class GuestCheckoutRequest(BaseModel):
    email: EmailStr
    nombre: str
    payment_method: str  # "anticipado" | "contraentrega"
    shipping_address: ShippingAddress
    items: List[CartItemInput]


def generate_temp_password(length: int = 10) -> str:
    """Genera una contraseña temporal legible."""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@router.post("/checkout")
async def guest_checkout(
    data: GuestCheckoutRequest,
    db: Session = Depends(get_db)
):
    """
    Procesa un checkout de invitado.
    - Verifica stock de todos los productos
    - Busca o crea usuario con el email
    - Crea la orden con los items
    - Envía emails de confirmación
    """

    if not data.items:
        raise HTTPException(status_code=400, detail="El carrito está vacío")

    # ── 1. Verificar productos y calcular total ────────────────────────────────
    order_items_data = []
    total = 0.0

    for item in data.items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.is_active == True
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Producto no encontrado: {item.product_id}"
            )
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para '{product.name}'. Disponible: {product.stock}"
            )

        subtotal = product.price * item.quantity
        total += subtotal
        order_items_data.append({
            "product": product,
            "quantity": item.quantity,
            "unit_price": product.price,
            "name": product.name
        })

    # ── 2. Buscar o crear usuario ──────────────────────────────────────────────
    user = db.query(User).filter(User.email == data.email).first()
    cuenta_nueva = False
    temp_password = None

    if not user:
        # Crear cuenta automáticamente
        temp_password = generate_temp_password()
        user = User(
            email=data.email,
            full_name=data.nombre,
            hashed_password=hash_password(temp_password),
            is_active=True,
            is_admin=False
        )
        db.add(user)
        db.flush()
        cuenta_nueva = True

    # ── 3. Crear la orden ──────────────────────────────────────────────────────
    order = Order(
        user_id=user.id,
        status="pending" if data.payment_method == "contraentrega" else "pending_payment",
        total_amount=total,
        payment_method=data.payment_method,
        guest_email=data.email,
        guest_name=data.nombre,
        shipping_address=json.dumps(data.shipping_address.model_dump())
    )
    db.add(order)
    db.flush()

    # ── 4. Crear items de la orden y descontar stock ───────────────────────────
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"]
        )
        db.add(order_item)
        item_data["product"].stock -= item_data["quantity"]

    db.commit()
    db.refresh(order)

    # ── 5. Enviar emails ───────────────────────────────────────────────────────
    nombre_corto = data.nombre.split()[0]

    # Email de bienvenida si es cuenta nueva
    if cuenta_nueva and temp_password:
        email_bienvenida(data.email, nombre_corto, temp_password)

    # Email de confirmación de orden
    email_confirmacion_orden(
        to=data.email,
        nombre=nombre_corto,
        order_id=str(order.id),
        items=order_items_data,
        total=total,
        metodo=data.payment_method
    )

    return {
        "order_id": str(order.id),
        "total": total,
        "payment_method": data.payment_method,
        "cuenta_creada": cuenta_nueva,
        "mensaje": "Pedido creado exitosamente"
    }