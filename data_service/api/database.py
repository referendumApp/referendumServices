from common.database.referendum import connection


def get_db():
    db = connection.SessionLocal()
    try:
        yield db
    finally:
        db.close()
