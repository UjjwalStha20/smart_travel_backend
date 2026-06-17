from .config import settings 
from sqlmodel import SQLModel, create_engine, Session
import app.models

DATABASE_URL = settings.database_url
print(f"Connecting to database ")

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session