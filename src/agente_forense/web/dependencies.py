"""
Inyección de dependencias para FastAPI.
"""

from typing import Generator
from sqlalchemy.orm import Session
from agente_forense.persistence.database import DatabaseEngine
from agente_forense.persistence.config import DatabaseConfig

def get_db_session() -> Generator[Session, None, None]:
    db_config = DatabaseConfig()
    db_engine = DatabaseEngine(db_config)
    session = db_engine.SessionLocal()
    try:
        yield session
    finally:
        session.close()
