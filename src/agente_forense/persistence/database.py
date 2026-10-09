"""
Módulo de gestión de conexión y sesiones con SQLAlchemy / PostgreSQL.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from agente_forense.persistence.config import DatabaseConfig


class Base(DeclarativeBase):
    """Clase base declarativa SQLAlchemy."""
    pass


class DatabaseEngine:
    """Administrador de motor SQLAlchemy y fábrica de sesiones."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = create_engine(
            config.connection_string,
            pool_pre_ping=True,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provee un contexto de transacción gestionado. Realiza rollback automático ante errores."""
        session: Session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def check_connection(self) -> bool:
        """Verifica conectividad real a PostgreSQL 18.6."""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return result == 1
