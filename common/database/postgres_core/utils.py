import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_connection_string(db_name: str):
    if not db_name:
        raise ValueError("Missing db_name")

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")

    if not user:
        raise ValueError(f"POSTGRES_USER environment variable is not set")
    if not password:
        raise ValueError(f"POSTGRES_PASSWORD environment variable is not set")
    if not host:
        raise ValueError(f"POSTGRES_HOST environment variable is not set")
    if not port:
        port = 5432

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def create_session(db_name: str):
    connection_string = get_connection_string(db_name)

    logger.info(f"Creating engine for database: {connection_string}")
    engine = create_engine(
        connection_string,
        pool_size=10,
        max_overflow=20,
        # Add connection timeouts
        connect_args={
            "connect_timeout": 30,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info(f"Successfully connected to database")
    except SQLAlchemyError as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
