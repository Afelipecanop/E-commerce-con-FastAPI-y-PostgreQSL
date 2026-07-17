from sqlalchemy.orm import Session
from models.settings import StoreSetting

DEFAULT_TRM = 4200.0


def get_setting(db: Session, key: str, default: str = None):
    setting = db.query(StoreSetting).filter(StoreSetting.key == key).first()
    return setting.value if setting else default


def get_current_trm(db: Session) -> float:
    """
    Lee la TRM guardada en store_settings (key='trm_usd_cop').
    Si no existe o no es un número válido, usa un valor de respaldo.
    """
    raw = get_setting(db, "trm_usd_cop")
    try:
        return float(raw) if raw else DEFAULT_TRM
    except (TypeError, ValueError):
        return DEFAULT_TRM