from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
import stripe
import os
from dotenv import load_dotenv

from database import get_db
from models.cart import Cart, CartItem
from models.order import Order, OrderItem
from models.product import Product
from schemas.order import OrderResponse, CheckoutResponse
from middleware.auth import get_current_user

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

router = APIRouter(prefix="/payments", tags=["Pagos"])


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Convierte el carrito en una sesión de pago de Stripe.
    Crea la orden en la DB con status 'pending' y devuelve
    la URL de pago de Stripe.
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
        total_amount=total
    )
    db.add(order)
    db.flush()

    # 5. Crear los items de la orden
    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.product.price  # Precio al momento de la compra
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    # 6. Crear sesión de pago en Stripe
    try:
        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item.product.name,
                        "description": item.product.description or "",
                    },
                    "unit_amount": int(item.product.price * 100),  # Stripe usa centavos
                },
                "quantity": item.quantity,
            }
            for item in cart.items
        ]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=f"{FRONTEND_URL}/checkout.html?success=true&order_id={order.id}",
            cancel_url=f"{FRONTEND_URL}/checkout.html?cancelled=true",
            metadata={"order_id": str(order.id)}  # Guardamos el ID para el webhook
        )

    except stripe.StripeError as e:
        # Si Stripe falla, cancelamos la orden
        order.status = "cancelled"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al crear sesión de pago: {str(e)}"
        )

    # 7. Guardar el ID de la sesión Stripe en la orden
    order.stripe_payment_id = checkout_session.id
    db.commit()

    return CheckoutResponse(
        checkout_url=checkout_session.url,
        order_id=str(order.id)
    )


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe llama a este endpoint cuando ocurre un evento de pago.
    Aquí confirmamos el pago y actualizamos el stock y la orden.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # Verificar que el webhook realmente viene de Stripe
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido")
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma inválida")

    # Procesar el evento de pago exitoso
    if event["type"] == "checkout.session.completed":
      session = event["data"]["object"]
       
      # Acceso compatible con versiones nuevas de Stripe
    metadata = session.get("metadata") if isinstance(session, dict) else session.metadata
    order_id = metadata.get("order_id") if isinstance(metadata, dict) else metadata["order_id"]

    if order_id:
        from uuid import UUID as PyUUID
        try:
            order_uuid = PyUUID(order_id)
        except ValueError:
            return {"status": "invalid order_id"}

        order = db.query(Order).filter(Order.id == order_uuid).first()
        if order and order.status == "pending":

            # Marcar la orden como pagada
            order.status = "paid"
            db.commit()

            # Descontar el stock de cada producto
            for item in order.items:
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).first()
                if product:
                    product.stock -= item.quantity
                    db.commit()

            # Vaciar el carrito del usuario
            cart = db.query(Cart).filter(
                Cart.user_id == order.user_id
            ).first()
            if cart:
                for cart_item in cart.items:
                    db.delete(cart_item)
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