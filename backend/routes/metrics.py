from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from database import get_db
from models.order import Order, OrderItem
from models.product import Product
from models.user import User
from models.cart import Cart, CartItem
from middleware.auth import get_current_admin

router = APIRouter(prefix="/metrics", tags=["Métricas"])


@router.get("/dashboard")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """
    Devuelve todas las métricas clave del negocio para el panel admin.
    Solo administradores.
    """
    now = datetime.utcnow()
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_semana = now - timedelta(days=now.weekday())
    hace_30_dias = now - timedelta(days=30)
    hace_60_dias = now - timedelta(days=60)

    # ── VENTAS ────────────────────────────────────────────────────────────────

    # Total ventas pagadas (histórico)
    total_ventas = db.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(Order.status == "paid").scalar()

    # Ventas este mes
    ventas_mes = db.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        Order.status == "paid",
        Order.created_at >= inicio_mes
    ).scalar()

    # Ventas últimos 30 días
    ventas_30d = db.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        Order.status == "paid",
        Order.created_at >= hace_30_dias
    ).scalar()

    # Ventas 30-60 días atrás (para comparar)
    ventas_30_60d = db.query(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).filter(
        Order.status == "paid",
        Order.created_at >= hace_60_dias,
        Order.created_at < hace_30_dias
    ).scalar()

    # Variación porcentual ventas
    if ventas_30_60d > 0:
        variacion_ventas = ((ventas_30d - ventas_30_60d) / ventas_30_60d) * 100
    else:
        variacion_ventas = 100.0 if ventas_30d > 0 else 0.0

    # ── ÓRDENES ───────────────────────────────────────────────────────────────

    total_ordenes = db.query(Order).filter(Order.status == "paid").count()
    ordenes_mes = db.query(Order).filter(
        Order.status == "paid",
        Order.created_at >= inicio_mes
    ).count()
    ordenes_pendientes = db.query(Order).filter(Order.status == "pending").count()
    ordenes_canceladas = db.query(Order).filter(Order.status == "cancelled").count()

    # Ticket promedio
    ticket_promedio = float(total_ventas) / total_ordenes if total_ordenes > 0 else 0

    # ── USUARIOS ──────────────────────────────────────────────────────────────

    total_usuarios = db.query(User).filter(User.is_active == True).count()
    usuarios_mes = db.query(User).filter(
        User.is_active == True,
        User.created_at >= inicio_mes
    ).count()
    usuarios_30d = db.query(User).filter(
        User.is_active == True,
        User.created_at >= hace_30_dias
    ).count()
    usuarios_30_60d = db.query(User).filter(
        User.is_active == True,
        User.created_at >= hace_60_dias,
        User.created_at < hace_30_dias
    ).count()

    if usuarios_30_60d > 0:
        variacion_usuarios = ((usuarios_30d - usuarios_30_60d) / usuarios_30_60d) * 100
    else:
        variacion_usuarios = 100.0 if usuarios_30d > 0 else 0.0

    # ── PRODUCTOS ─────────────────────────────────────────────────────────────

    total_productos = db.query(Product).filter(Product.is_active == True).count()
    productos_sin_stock = db.query(Product).filter(
        Product.is_active == True,
        Product.stock == 0
    ).count()
    productos_bajo_stock = db.query(Product).filter(
        Product.is_active == True,
        Product.stock > 0,
        Product.stock <= 5
    ).count()

    # ── TOP PRODUCTOS ─────────────────────────────────────────────────────────

    top_productos = db.query(
        Product.id,
        Product.name,
        Product.price,
        Product.stock,
        func.sum(OrderItem.quantity).label("total_vendido"),
        func.sum(OrderItem.quantity * OrderItem.unit_price).label("total_ingresos")
    ).join(
        OrderItem, OrderItem.product_id == Product.id
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.status == "paid"
    ).group_by(
        Product.id, Product.name, Product.price, Product.stock
    ).order_by(
        desc("total_vendido")
    ).limit(5).all()

    # ── CARRITOS ──────────────────────────────────────────────────────────────

    carritos_con_items = db.query(Cart).join(
        CartItem, CartItem.cart_id == Cart.id
    ).distinct().count()

    # ── VENTAS POR DÍA (últimos 14 días) ─────────────────────────────────────

    ventas_por_dia = []
    for i in range(13, -1, -1):
        dia = now - timedelta(days=i)
        inicio_dia = dia.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_dia = inicio_dia + timedelta(days=1)

        monto = db.query(
            func.coalesce(func.sum(Order.total_amount), 0)
        ).filter(
            Order.status == "paid",
            Order.created_at >= inicio_dia,
            Order.created_at < fin_dia
        ).scalar()

        ordenes_dia = db.query(Order).filter(
            Order.status == "paid",
            Order.created_at >= inicio_dia,
            Order.created_at < fin_dia
        ).count()

        ventas_por_dia.append({
            "fecha": dia.strftime("%d/%m"),
            "monto": float(monto),
            "ordenes": ordenes_dia
        })

    # ── ÓRDENES RECIENTES ─────────────────────────────────────────────────────

    ordenes_recientes = db.query(Order).filter(
        Order.status.in_(["paid", "pending", "cancelled"])
    ).order_by(desc(Order.created_at)).limit(8).all()

    ordenes_recientes_data = []
    for o in ordenes_recientes:
        user = db.query(User).filter(User.id == o.user_id).first()
        ordenes_recientes_data.append({
            "id": str(o.id)[:8],
            "usuario": user.full_name if user else "—",
            "email": user.email if user else "—",
            "total": float(o.total_amount),
            "status": o.status,
            "fecha": o.created_at.strftime("%d/%m/%Y %H:%M") if o.created_at else "—"
        })

    return {
        "ventas": {
            "total_historico": float(total_ventas),
            "este_mes": float(ventas_mes),
            "ultimos_30d": float(ventas_30d),
            "variacion_pct": round(variacion_ventas, 1)
        },
        "ordenes": {
            "total": total_ordenes,
            "este_mes": ordenes_mes,
            "pendientes": ordenes_pendientes,
            "canceladas": ordenes_canceladas,
            "ticket_promedio": round(ticket_promedio, 2)
        },
        "usuarios": {
            "total": total_usuarios,
            "este_mes": usuarios_mes,
            "ultimos_30d": usuarios_30d,
            "variacion_pct": round(variacion_usuarios, 1)
        },
        "productos": {
            "total_activos": total_productos,
            "sin_stock": productos_sin_stock,
            "bajo_stock": productos_bajo_stock
        },
        "carritos": {
            "activos": carritos_con_items
        },
        "top_productos": [
            {
                "id": str(p.id),
                "nombre": p.name,
                "precio": float(p.price),
                "stock": p.stock,
                "total_vendido": int(p.total_vendido),
                "total_ingresos": float(p.total_ingresos)
            }
            for p in top_productos
        ],
        "ventas_por_dia": ventas_por_dia,
        "ordenes_recientes": ordenes_recientes_data
    }