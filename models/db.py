import os
from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine
from backend.config import settings

# Ensure data directory exists if using relative sqlite path
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "")
    parent_dir = Path(db_path).parent
    if parent_dir and not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, echo=False, connect_args={"check_same_thread": False})


def create_db(custom_engine=None):
    target_engine = custom_engine or engine
    SQLModel.metadata.create_all(target_engine)


def get_session(custom_engine=None):
    target_engine = custom_engine or engine
    with Session(target_engine) as session:
        yield session
