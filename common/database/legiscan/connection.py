import os

from common.database.postgres_core.utils import create_session

SessionLocal = create_session(db_name=os.getenv("LEGISCAN_API_DB_NAME"))
