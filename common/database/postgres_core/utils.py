import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_connection_string(db_name: str):
    if not db_name:
        raise ValueError(
            f"Missing required database configuration: {', '.join(missing)}"
        )

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")

    print(f"Attempting database connection with:")
    print(f"User: {user}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"DB Name: {db_name}")

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
    engine = create_engine(connection_string, pool_size=10, max_overflow=20)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
