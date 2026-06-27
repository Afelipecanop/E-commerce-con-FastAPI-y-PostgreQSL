from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
import uuid
import httpx
import os
import requests as http_requests

from database import get_db
from models.layout import StoreLayout
from schemas.layout import LayoutUpdate, BlockResponse, BlockConfig, AIGenerateRequest
from middleware.auth import get_current_admin

router = APIRouter(prefix="/layout", tags=["Layout de la tienda"])


@router.post("/generate-block")
async def generate_block(
    request: dict,
    admin=Depends(get_current_admin)
):
    """Genera HTML/CSS con IA para un bloque personalizado."""
    prompt = request.get("prompt", "")
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        raise HTTPException(status_code=500, detail="Asistente IA no configurado")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": f"""Eres un experto en HTML y CSS para e-commerce.
Genera una sección HTML/CSS profesional para una tienda online.

La sección debe:
- Tener diseño moderno y limpio
- Usar colores que combinen con azul (#2563eb) como color primario
- Ser responsive
- NO usar frameworks externos (solo HTML y CSS puro)

El usuario quiere: "{prompt}"

Responde SOLO con un objeto JSON con esta estructura exacta, sin explicaciones ni markdown:
{{"html": "el HTML completo aquí", "css": "el CSS adicional aquí"}}"""
                }]
            },
            timeout=30.0
        )
        
        data = response.json()
        text = data["content"][0]["text"]
        
        try:
            import json
            clean = text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean)
        except:
            parsed = {"html": text, "css": ""}
            
        return parsed

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


@router.post("/ai-generate")
def ai_generate(
    data: AIGenerateRequest,
    admin=Depends(get_current_admin)
):
    """Genera HTML/CSS con IA para bloques personalizados. Solo administradores."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="Asistente IA no configurado (falta ANTHROPIC_API_KEY)")

    system_prompt = (
        "Eres un experto en HTML y CSS para e-commerce. "
        "Genera una sección HTML/CSS profesional para una tienda online. "
        "La sección debe: tener diseño moderno y limpio, usar colores que combinen con azul (#2563eb) como color primario, "
        "ser responsive, NO usar frameworks externos (solo HTML y CSS puro). "
        "Responde SOLO con un objeto JSON con esta estructura exacta, sin explicaciones ni markdown: "
        '{"html": "el HTML completo aquí", "css": "el CSS adicional aquí si lo separaste"}. '
        "El HTML puede incluir estilos inline o una etiqueta <style> interna."
    )

    try:
        resp = http_requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1500,
                "system": system_prompt,
                "messages": [{"role": "user", "content": data.prompt}],
            },
            timeout=30,
        )
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="El servicio de IA tardó demasiado, intenta de nuevo")
    except http_requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="No se pudo contactar el servicio de IA")

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Error al generar contenido con IA")

    text = resp.json()["content"][0]["text"]
    try:
        clean = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
    except Exception:
        parsed = {"html": text, "css": ""}

    return {"html": parsed.get("html", ""), "css": parsed.get("css", "")}
