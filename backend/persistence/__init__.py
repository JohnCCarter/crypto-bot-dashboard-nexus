import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# DATABASE_URL prioritises env value; fallback to local sqlite for tests
# Use absolute path to avoid SQLite database file location issues
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
default_db_path = f"sqlite:///{os.path.join(project_root, 'local.db')}"
DATABASE_URL = os.getenv("DATABASE_URL", default_db_path)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

Base = declarative_base()

__all__ = [
    "SessionLocal",
    "engine",
    "Base",
]
