import logging

from .config import settings
from sqlmodel import SQLModel, create_engine, Session
import app.models

logger = logging.getLogger(__name__)

DATABASE_URL = settings.database_url
logger.info("Connecting to database")

engine = create_engine(DATABASE_URL, echo=settings.DB_ECHO)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine, expire_on_commit=False) as session:
        yield session