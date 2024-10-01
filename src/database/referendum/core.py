import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Get the DATABASE_URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/local-db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
