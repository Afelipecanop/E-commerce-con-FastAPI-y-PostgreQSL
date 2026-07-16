from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import httpx

from database import get_db
from models.settings import StoreSetting
from middleware.auth import get_current_admin

router = APIRouter(prefix="/settings", tags=["Ajustes de la tienda"])

# Valores por defecto
DEFAULTS = {
    "store_name": "Velonox",
    "store_slogan": "Cocina de por vida.",
    "primary_color": "#1D7A4F",
    "secondary_color": "#0F1A14",
    "font_family": "DM Sans",
    "logo_url": "",
    "banner_url": "",
    "banner_title": "Cocina de",
    "banner_subtitle": "por vida.",
    "trm_usd_cop": "4200",
    "trm_auto": "true",
}


def get_all_settings(db: Session) -> dict:
    """Lee todos los ajustes de la DB y completa los que falten con defaults."""
    rows = db.query(StoreSetting).all()
    settings = {row.key: row.value for row in rows}
    for key, default in DEFAULTS.items():
        if key not in settings:
            settings[key] = default
    return settings


@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    """Devuelve los ajustes actuales de la tienda. Público."""
    return get_all_settings(db)


@router.put("/")
def update_settings(
    data: dict,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Actualiza los ajustes de la tienda. Solo administradores."""
    for key, value in data.items():
        existing = db.query(StoreSetting).filter(StoreSetting.key == key).first()
        if existing:
            existing.value = str(value)
        else:
            db.add(StoreSetting(key=key, value=str(value)))
    db.commit()
    return {"mensaje": "Ajustes guardados ✅"}


@router.get("/trm")
async def get_trm(db: Session = Depends(get_db)):
    """
    Devuelve la tasa de cambio USD → COP.
    Si trm_auto es true intenta obtenerla de API externa.
    Si falla usa la tasa manual.
    """
    settings = get_all_settings(db)
    trm_manual = float(settings.get("trm_usd_cop", 4200))
    trm_auto = settings.get("trm_auto", "true") == "true"

    if trm_auto:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    "https://api.exchangerate-api.com/v4/latest/USD",
                    timeout=5.0
                )
                data = res.json()
                trm_live = data["rates"].get("COP", trm_manual)
                return {
                    "trm": round(trm_live, 2),
                    "source": "auto",
                    "manual": trm_manual
                }
        except Exception:
            pass

    return {
        "trm": trm_manual,
        "source": "manual",
        "manual": trm_manual
    }


@router.put("/trm")
def update_trm(
    data: dict,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Actualiza la TRM manual y el modo auto. Solo administradores."""
    if "trm" in data:
        existing = db.query(StoreSetting).filter(
            StoreSetting.key == "trm_usd_cop"
        ).first()
        if existing:
            existing.value = str(data["trm"])
        else:
            db.add(StoreSetting(key="trm_usd_cop", value=str(data["trm"])))

    if "auto" in data:
        existing = db.query(StoreSetting).filter(
            StoreSetting.key == "trm_auto"
        ).first()
        if existing:
            existing.value = "true" if data["auto"] else "false"
        else:
            db.add(StoreSetting(
                key="trm_auto",
                value="true" if data["auto"] else "false"
            ))

    db.commit()
    return {"mensaje": "TRM actualizada"}