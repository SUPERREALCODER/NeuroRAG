from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Replace with your real credentials
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:manashama_24@localhost:5432/world"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
