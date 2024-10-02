import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def get_connection_string():
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('REFERENDUM_DB_NAME')}"
    )


connection_string = get_connection_string()
engine = create_engine(connection_string)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
