import hashlib
import hmac
import base64
import os

BOLD_SECRET_KEY = os.getenv("C0p6GYPda4SU83qoYYs9ZwCN5Dr9KfsiVUg9Th0OUl4")


def usd_to_cop(amount_usd: float, trm: float) -> int:
    """Convierte un monto en USD a COP (entero, sin decimales) usando la TRM dada."""
    return round(amount_usd * trm)


def generate_integrity_signature(order_id: str, amount: int, currency: str = "COP") -> str:
    """
    Genera el hash de integridad que exige Bold para el botón de pagos.
    Formato exacto exigido por Bold: {order_id}{amount}{currency}{secret_key}
    """
    concatenated = f"{order_id}{amount}{currency}{BOLD_SECRET_KEY}"
    return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()


def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Verifica la firma del webhook de Bold (header X-Bold-Signature).
    Bold hace: HMAC-SHA256( base64(raw_body), secret_key ) en hex.
    """
    if not signature_header:
        return False
    encoded_body = base64.b64encode(raw_body)
    expected = hmac.new(
        BOLD_SECRET_KEY.encode("utf-8"),
        encoded_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)