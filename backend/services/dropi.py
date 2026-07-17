import httpx
import os
import logging

DROPI_BASE_URL = os.getenv("DROPI_BASE_URL")
DROPI_API_KEY = os.getenv("DROPI_API_KEY")
logger = logging.getLogger("velonox.dropi")

HEADERS = {
    "dropi-integracion-key": DROPI_API_KEY or "",
    "Content-Type": "application/json",
}


def create_dropi_order(order, order_items, is_cod: bool) -> dict:
    """
    Crea la orden de envío en Dropi.
    TODO: ajustar el payload y el endpoint exacto cuando Dropi confirme su documentación.
    """
    if not DROPI_BASE_URL or not DROPI_API_KEY:
        raise RuntimeError("Dropi no está configurado todavía (faltan DROPI_BASE_URL / DROPI_API_KEY)")

    payload = {
        "EnvioConCobro": is_cod,
        "amount": int(order.total_amount),
        "cliente": {
            "nombre": order.guest_name or (order.user.full_name if order.user else None),
            "telefono": order.customer_phone,
            "email": order.guest_email or (order.user.email if order.user else None),
            "tipo_documento": order.document_type,
            "numero_documento": order.document_number,
        },
        "direccion_destino": order.shipping_address,
        "notas_envio": order.shipping_notes,
        "ciudad_destino": {"cod_dane": order.city_dane_code},  # queda null hasta tener el mapeo de ciudades
        "productos": [
            {
                "id_producto_dropi": getattr(item.product, "dropi_product_id", None),
                "cantidad": item.quantity,
            }
            for item in order_items
        ],
    }

    response = httpx.post(
        f"{DROPI_BASE_URL}/integrations/orders/create",  # ⚠️ confirmar endpoint real
        json=payload,
        headers=HEADERS,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()