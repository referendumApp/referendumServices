from sqlalchemy.orm import Session

from common.database.referendum import models, schemas


### USERS ###


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(name=user.name, email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def update_user(db: Session, db_user: models.User):
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db.query(models.User).filter(models.User.id == user_id).delete()
    db.commit()
    return


### BILLS ###


def create_bill(db: Session, bill: schemas.BillCreate):
    db_bill = models.Bill(
        legiscan_id=bill.legiscan_id,
        identifier=bill.identifier,
        title=bill.title,
        description=bill.description,
        state=bill.state,
        body=bill.body,
        session=bill.session,
        briefing=bill.briefing,
        status=bill.status,
        latestAction=bill.latestAction,
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill


def get_bill(db: Session, bill_id: int):
    return db.query(models.Bill).filter(models.Bill.id == bill_id).first()


def get_bills(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Bill).offset(skip).limit(limit).all()


def get_bill_by_legiscan_id(db: Session, legiscan_id: int):
    return db.query(models.Bill).filter(models.Bill.legiscan_id == legiscan_id).first()


def update_bill(db: Session, db_bill: models.Bill):
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill


def delete_bill(db: Session, bill_id: int):
    db.query(models.Bill).filter(models.Bill.id == bill_id).delete()
    db.commit()
    return


# ### LEGISLATORS ###


def create_legislator(db: Session, legislator: schemas.LegislatorCreate):
    db_legislator = models.Legislator(**legislator.model_dump())
    db.add(db_legislator)
    db.commit()
    db.refresh(db_legislator)
    return db_legislator


def get_legislator(db: Session, legislator_id: int):
    return db.query(models.Legislator).filter(models.Legislator.id == legislator_id).first()


def get_legislator_by_name_and_state(db: Session, name: str, state: str):
    return db.query(models.Legislator).filter(models.Legislator.name == name, models.Legislator.state == state).first()


def get_legislators(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Legislator).offset(skip).limit(limit).all()


def update_legislator(db: Session, db_legislator: models.Legislator):
    db.add(db_legislator)
    db.commit()
    db.refresh(db_legislator)
    return db_legislator


def delete_legislator(db: Session, legislator_id: int):
    db.query(models.Legislator).filter(models.Legislator.id == legislator_id).delete()
    db.commit()
    return
