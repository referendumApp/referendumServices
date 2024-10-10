import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_connection_string(db_name: str):
    return (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{db_name}"
    )


def create_session(db_name: str):
    connection_string = get_connection_string(db_name)
    engine = create_engine(connection_string, pool_size=10, max_overflow=20)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
