from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
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


@router.get("/render", response_class=HTMLResponse)
def render_page(db: Session = Depends(get_db)):
    """
    Renderiza la página principal completa con el layout actual.
    Público — se usa para el preview en tiempo real del editor.
    """
    blocks = db.query(StoreLayout).order_by(StoreLayout.order_index).all()
    
    if not blocks:
        blocks = []
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

    blocks_html = ""
    for block in blocks:
        if block.is_visible:
            config = json.loads(block.config)
            block_html = render_block(block.block_type, config)
            blocks_html += block_html

    # HTML base de la página (estilo Velonox de index.html)
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Velonox — Cocina de por vida</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'DM Sans', sans-serif; background: #F5F5F3; color: #0F1A14; }}
        
        /* NAV */
        .nav {{ background: #0F1A14; padding: 0 2rem; display: flex; align-items: center; justify-content: space-between; height: 56px; position: sticky; top: 0; z-index: 100; }}
        .nav-logo {{ display: flex; align-items: baseline; gap: 0; text-decoration: none; }}
        .nav-logo span.a {{ font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; color: #C8D8C0; letter-spacing: -.5px; }}
        .nav-logo span.b {{ font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; color: #1D7A4F; letter-spacing: -.5px; }}
        .nav-links {{ display: flex; gap: 1.5rem; }}
        .nav-links a {{ font-size: 13px; color: #C8D8C0; text-decoration: none; opacity: .7; transition: opacity .2s; }}
        .nav-links a:hover {{ opacity: 1; }}
        .nav-right {{ display: flex; gap: 12px; align-items: center; }}
        .nav-icon {{ color: #C8D8C0; opacity: .7; font-size: 18px; cursor: pointer; transition: opacity .2s; text-decoration: none; }}
        .nav-icon:hover {{ opacity: 1; }}
        
        /* GENERAL */
        .sec {{ padding: 3.5rem 2rem; }}
        .sec-title {{ font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 700; color: #0F1A14; margin-bottom: 2rem; }}
        .btn-primary {{ background: #1D7A4F; color: #F5F5F3; font-size: 14px; font-weight: 500; padding: 12px 28px; border-radius: 2px; border: none; cursor: pointer; font-family: 'DM Sans', sans-serif; letter-spacing: .02em; transition: background .2s; }}
        .btn-primary:hover {{ background: #22904F; }}
        
        /* CUSTOM BLOCKS */
        .custom-block {{ padding: 2rem; }}
    </style>
</head>
<body>

<!-- NAV -->
<nav class="nav">
    <a href="/" class="nav-logo"><span class="a">Velo</span><span class="b">nox</span></a>
    <div class="nav-links">
        <a href="#">Cocina</a>
        <a href="#">Sets</a>
        <a href="#">Regalos</a>
        <a href="#">Nosotros</a>
    </div>
    <div class="nav-right">
        <a href="#" class="nav-icon ti ti-shopping-bag" aria-label="Carrito"></a>
        <a href="#" class="nav-icon ti ti-user" aria-label="Ingresar"></a>
    </div>
</nav>

<!-- BLOQUES DINÁMICOS -->
{blocks_html}

<!-- FOOTER PREDETERMINADO -->
<footer style="background: #0F1A14; color: #C8D8C0; padding: 2rem; border-top: 1px solid #1A2820; text-align: center;">
    <p style="font-size: 0.85rem; color: #4A6A5A;">© 2025 Velonox. Todos los derechos reservados.</p>
</footer>

</body>
</html>"""

    return html


def render_block(block_type: str, config: dict) -> str:
    """Renderiza un bloque individual como HTML."""
    
    if block_type == "announcement_bar":
        return f"""<div style="background:{config.get('background_color','#2563eb')};color:{config.get('text_color','#fff')};text-align:center;padding:0.8rem;font-size:0.9rem;font-weight:500">
            {config.get('text', 'Anuncio')}
        </div>"""
    
    elif block_type == "hero_banner":
        return f"""<section style="background:{config.get('background_color','#1e293b')};color:{config.get('text_color','#fff')};min-height:480px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:4rem 2rem">
            <h1 style="font-family:'Playfair Display',serif;font-size:clamp(40px,8vw,72px);font-weight:900;margin-bottom:1rem;line-height:.95">{config.get('title','Bienvenido')}</h1>
            <p style="font-size:1.1rem;margin-bottom:2rem;max-width:500px;opacity:.9">{config.get('subtitle','Descubre nuestra colección')}</p>
            <button class="btn-primary">{config.get('button_text','Ver productos')}</button>
        </section>"""
    
    elif block_type == "product_grid":
        cols = config.get('columns', 3)
        limit = config.get('limit', 6)
        return f"""<section class="sec" style="background:#F5F5F3">
            <h2 class="sec-title">{config.get('title', 'Nuestros productos')}</h2>
            <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:1.2rem">
                {(''.join([f'<div style="background:#fff;border:1px solid #E8E8E4;border-radius:8px;overflow:hidden;padding:1rem;text-align:center"><div style="width:100%;height:150px;background:#E8ECE6;border-radius:6px;margin-bottom:0.8rem;display:flex;align-items:center;justify-content:center;font-size:2rem">🛍️</div><h3 style="color:#0F1A14;margin-bottom:0.4rem">Producto</h3><p style="color:#7A7A72;margin-bottom:0.8rem">Descripción</p><p style="font-size:1.1rem;font-weight:600;color:#0F1A14;margin-bottom:0.8rem">$99.99</p><button class="btn-primary" style="width:100%">Agregar</button></div>') for _ in range(limit)])}
            </div>
        </section>"""
    
    elif block_type == "text_section":
        return f"""<section class="sec" style="background:{config.get('background_color','#f8fafc')}">
            <h2 class="sec-title" style="text-align:{config.get('text_align','center')}">{config.get('title','Sobre nosotros')}</h2>
            <p style="text-align:{config.get('text_align','center')};color:#64748b;font-size:1rem;max-width:700px;margin:0 auto;line-height:1.7">{config.get('content','')}</p>
        </section>"""
    
    elif block_type == "testimonials":
        items = config.get('items', [])
        items_html = ''.join([f'<div style="background:#fff;border-radius:8px;padding:1.5rem;text-align:center"><div style="color:#F59E0B;margin-bottom:0.5rem;font-size:1.2rem">{"⭐"*int(item.get("rating",5))}</div><p style="color:#475569;font-size:0.95rem;margin-bottom:1rem;line-height:1.6">"{item.get("text","Testimonio")}"</p><strong style="color:#0F1A14">{item.get("name","Cliente")}</strong></div>' for item in items])
        return f"""<section class="sec" style="background:#1A2820">
            <h2 class="sec-title" style="color:#C8D8C0;text-align:center">{config.get('title','Testimonios')}</h2>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.5rem;max-width:1000px;margin:0 auto">
                {items_html}
            </div>
        </section>"""
    
    elif block_type == "footer":
        return f"""<footer style="background:{config.get('background_color','#0F1A14')};color:{config.get('text_color','#C8D8C0')};padding:2.5rem 2rem;text-align:center;border-top:1px solid #1A2820">
            <h3 style="font-size:1.2rem;margin-bottom:0.5rem">{config.get('store_name','Velonox')}</h3>
            <p style="font-size:0.9rem;margin-bottom:0.8rem">{config.get('tagline','Tu tienda')}</p>
            <p style="font-size:0.85rem">✉️ {config.get('email','contacto@velonox.com')}</p>
            <p style="font-size:0.8rem;margin-top:1rem;opacity:0.6">© {json.loads(json.dumps({}).replace('{}', str(__import__('datetime').datetime.now().year)))} {config.get('store_name','Velonox')}</p>
        </footer>"""
    
    elif block_type == "custom_html":
        html = config.get('html', '')
        css = config.get('css', '')
        return f"""<div class="custom-block">
            <style>{css}</style>
            {html}
        </div>"""
    
    else:
        return f"""<div style="padding:2rem;text-align:center;color:#94a3b8;border:2px dashed #E2E8F0;margin:1rem">
            Bloque no reconocido: {block_type}
        </div>"""

