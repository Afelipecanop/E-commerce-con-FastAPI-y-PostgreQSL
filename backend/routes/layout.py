from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import json
import uuid

from database import get_db
from models.layout import StoreLayout
from schemas.layout import LayoutUpdate, BlockResponse
from middleware.auth import get_current_admin

router = APIRouter(prefix="/layout", tags=["Layout de la tienda"])

# Bloques por defecto que tiene la tienda al inicio
DEFAULT_BLOCKS = [
    {
        "id": "block-announcement",
        "block_type": "announcement_bar",
        "order_index": 0,
        "is_visible": True,
        "config": {
            "text": "🚚 Envío gratis en compras mayores a $50",
            "background_color": "#2563eb",
            "text_color": "#ffffff"
        }
    },
    {
        "id": "block-banner",
        "block_type": "hero_banner",
        "order_index": 1,
        "is_visible": True,
        "config": {
            "title": "Bienvenido a nuestra tienda",
            "subtitle": "Descubre nuestra colección exclusiva",
            "button_text": "Ver productos",
            "image_url": "",
            "background_color": "#1e293b",
            "text_color": "#ffffff"
        }
    },
    {
        "id": "block-products",
        "block_type": "product_grid",
        "order_index": 2,
        "is_visible": True,
        "config": {
            "title": "Nuestros productos",
            "columns": 3,
            "show_all": True,
            "limit": 6
        }
    },
    {
        "id": "block-text",
        "block_type": "text_section",
        "order_index": 3,
        "is_visible": False,
        "config": {
            "title": "Sobre nosotros",
            "content": "Somos una tienda dedicada a ofrecerte los mejores productos.",
            "background_color": "#f8fafc",
            "text_align": "center"
        }
    },
    {
        "id": "block-testimonials",
        "block_type": "testimonials",
        "order_index": 4,
        "is_visible": False,
        "config": {
            "title": "Lo que dicen nuestros clientes",
            "items": [
                {
                    "name": "María García",
                    "text": "Excelente servicio y productos de calidad.",
                    "rating": 5
                },
                {
                    "name": "Carlos López",
                    "text": "Muy buena experiencia de compra.",
                    "rating": 5
                }
            ]
        }
    },
    {
        "id": "block-footer",
        "block_type": "footer",
        "order_index": 5,
        "is_visible": True,
        "config": {
            "store_name": "Mi Tienda",
            "tagline": "Tu tienda de confianza",
            "email": "contacto@mitienda.com",
            "background_color": "#1e293b",
            "text_color": "#94a3b8"
        }
    }
]


@router.get("/", response_model=List[BlockResponse])
def get_layout(db: Session = Depends(get_db)):
    """
    Devuelve todos los bloques del layout ordenados.
    Si no hay bloques en la DB devuelve los bloques por defecto.
    Público — lo llama la tienda al cargar.
    """
    blocks = db.query(StoreLayout).order_by(StoreLayout.order_index).all()

    if not blocks:
        # Primera vez — inicializa con los bloques por defecto
        for block_data in DEFAULT_BLOCKS:
            block = StoreLayout(
                id=block_data["id"],
                block_type=block_data["block_type"],
                order_index=block_data["order_index"],
                is_visible=block_data["is_visible"],
                config=json.dumps(block_data["config"])
            )
            db.add(block)
        db.commit()
        blocks = db.query(StoreLayout).order_by(StoreLayout.order_index).all()

    # Parsear el config JSON antes de devolver
    result = []
    for block in blocks:
        result.append(BlockResponse(
            id=block.id,
            block_type=block.block_type,
            order_index=block.order_index,
            is_visible=block.is_visible,
            config=json.loads(block.config)
        ))

    return result


@router.put("/")
def update_layout(
    data: LayoutUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """
    Guarda el layout completo.
    Reemplaza todos los bloques existentes con los nuevos.
    Solo administradores.
    """
    # Borra los bloques actuales
    db.query(StoreLayout).delete()

    # Inserta los nuevos en el orden recibido
    for i, block in enumerate(data.blocks):
        new_block = StoreLayout(
            id=block.id if block.id else str(uuid.uuid4()),
            block_type=block.block_type,
            order_index=i,
            is_visible=block.is_visible,
            config=json.dumps(block.config)
        )
        db.add(new_block)

    db.commit()
    return {"mensaje": "Layout guardado ✅"}


@router.post("/blocks")
def add_block(
    block: BlockConfig,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Agrega un nuevo bloque al layout. Solo administradores."""
    # Obtener el índice más alto actual
    last = db.query(StoreLayout).order_by(
        StoreLayout.order_index.desc()
    ).first()
    next_index = (last.order_index + 1) if last else 0

    new_block = StoreLayout(
        id=str(uuid.uuid4()),
        block_type=block.block_type,
        order_index=next_index,
        is_visible=block.is_visible,
        config=json.dumps(block.config)
    )
    db.add(new_block)
    db.commit()
    db.refresh(new_block)

    return BlockResponse(
        id=new_block.id,
        block_type=new_block.block_type,
        order_index=new_block.order_index,
        is_visible=new_block.is_visible,
        config=json.loads(new_block.config)
    )


@router.delete("/blocks/{block_id}")
def delete_block(
    block_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Elimina un bloque del layout. Solo administradores."""
    block = db.query(StoreLayout).filter(StoreLayout.id == block_id).first()
    if block:
        db.delete(block)
        db.commit()
    return {"mensaje": "Bloque eliminado ✅"}
