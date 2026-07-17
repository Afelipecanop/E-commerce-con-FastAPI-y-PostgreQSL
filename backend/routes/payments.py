from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
import os
import logging
from dotenv import load_dotenv

from database import get_db
from models.cart import Cart, CartItem
from models.order import Order, OrderItem
from models.product import Product
from schemas.order import OrderResponse, CheckoutRequest
from middleware.auth import get_current_user
from services.bold import generate_integrity_signature, verify_webhook_signature, usd_to_cop
from services.email import email_confirmacion_orden
from services.dropi import create_dropi_order
from services.settings import get_current_trm

load_dotenv()

BOLD_API_KEY = os.getenv("BOLD_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

router = APIRouter(prefix="/payments", tags=["Pagos"])
logger = logging.getLogger("velonox.payments")


@router.post("/checkout")
def create_checkout(
    data: CheckoutRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Convierte el carrito en una orden. Según payment_method:
    - 'anticipado': crea la orden pending y devuelve los datos para el botón Bold.
    - 'contraentrega': confirma la orden de una vez y la envía a Dropi.
    """

    # 1. Obtener el carrito del usuario
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El carrito está vacío"
        )

    # 2. Verificar stock de todos los productos antes de procesar
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para '{product.name}'. Disponible: {product.stock}"
            )

    # 3. Calcular el total
    total = sum(item.product.price * item.quantity for item in cart.items)

    # 4. Crear la orden en la DB con status 'pending'
    order = Order(
        user_id=current_user.id,
        status="pending",
        total_amount=total,
        customer_phone=data.customer_phone,
        document_type=data.document_type,
        document_number=data.document_number,
        shipping_address=data.shipping_address,
        shipping_notes=data.shipping_notes,
        department_name=data.department_name,
        city_name=data.city_name,
        payment_method=data.payment_method.value,
    )
    db.add(order)
    db.flush()

    # 5. Crear los items de la orden
    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    # 6a. Flujo Bold (pago anticipado)
    if data.payment_method == "anticipado":
        order.bold_order_id = f"VLX-{str(order.id)[:8]}-{int(order.total_amount)}"
        db.commit()

        trm = get_current_trm(db)
        amount = usd_to_cop(order.total_amount, trm)
        signature = generate_integrity_signature(order.bold_order_id, amount, "COP")

        return {
            "flow": "bold",
            "order_id": str(order.id),
            "bold_order_id": order.bold_order_id,
            "amount": amount,
            "currency": "COP",
            "api_key": BOLD_API_KEY,
            "signature": signature,
            "redirection_url": f"{FRONTEND_URL}/pedido-confirmado.html?order_id={order.id}",
        }

    # 6b. Flujo contraentrega: confirma ya mismo y descuenta stock
    order.status = "cod_confirmed"
    for item in cart.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock = max(0, product.stock - item.quantity)

    for cart_item in cart.items:
        db.delete(cart_item)

    try:
        dropi_response = create_dropi_order(order, order.items, is_cod=True)
        order.dropi_order_id = dropi_response.get("id")
        order.dropi_status = "created"
    except Exception as e:
        logger.error(f"Dropi falló para orden {order.id}: {e}")
        order.dropi_status = "pending_manual"

    db.commit()
    return {"flow": "cod", "order_id": str(order.id), "status": "confirmado"}


@router.post("/bold/webhook")
async def bold_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Bold llama a este endpoint cuando confirma un pago.
    Verifica la firma, marca la orden como pagada, descuenta stock,
    vacía el carrito y crea la orden en Dropi.
    """
    raw_body = await request.body()
    signature = request.headers.get("x-bold-signature", "")

    if not verify_webhook_signature(raw_body, signature):
        raise HTTPException(status_code=400, detail="Firma inválida")

    payload = await request.json()
    # TODO: confirmar la forma exacta del payload con un evento de prueba real
    payment_data = payload.get("data", {}).get("payment", {})
    bold_order_id = payment_data.get("order_id")
    tx_status = payment_data.get("status")

    if not bold_order_id:
        return {"status": "ignored"}

    order = db.query(Order).filter(Order.bold_order_id == bold_order_id).first()
    if not order:
        return {"status": "order not found"}

    if tx_status == "approved" and order.status == "pending":
        order.status = "paid"
        db.commit()

        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock = max(0, product.stock - item.quantity)
        db.commit()

        cart = db.query(Cart).filter(Cart.user_id == order.user_id).first()
        if cart:
            for cart_item in cart.items:
                db.delete(cart_item)
            db.commit()

        try:
            dropi_response = create_dropi_order(order, order.items, is_cod=False)
            order.dropi_order_id = dropi_response.get("id")
            order.dropi_status = "created"
        except Exception as e:
            logger.error(f"Dropi falló para orden {order.id}: {e}")
            order.dropi_status = "pending_manual"
        db.commit()

        # Enviar email de confirmación (funciona igual para usuario logueado o invitado)
        try:
            recipient_email = order.guest_email or (order.user.email if order.user else None)
            recipient_name = order.guest_name or (order.user.full_name if order.user else "Cliente")
            if recipient_email:
                email_confirmacion_orden(
                    to=recipient_email,
                    nombre=recipient_name.split()[0],
                    order_id=str(order.id),
                    items=[{"product": i.product, "quantity": i.quantity,
                            "unit_price": i.unit_price, "name": i.product.name}
                            for i in order.items],
                    total=order.total_amount,
                    metodo="anticipado"
                )
        except Exception as e:
            logger.error(f"Email de confirmación falló para orden {order.id}: {e}")

    elif tx_status in ("rejected", "failed") and order.status == "pending":
        order.status = "cancelled"
        db.commit()

    return {"status": "ok"}


@router.get("/orders", response_model=List[OrderResponse])
def get_my_orders(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Devuelve el historial de órdenes del usuario autenticado."""
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).all()
    return orders


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Devuelve el detalle de una orden específica del usuario."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada"
        )
    return order