from sqlalchemy.orm import Session

from . import orms, pydantic_models


### USERS ###


def create_user(db: Session, user: pydantic_models.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = orms.User(name=user.name, email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int):
    return db.query(orms.User).filter(orms.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(orms.User).filter(orms.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(orms.User).offset(skip).limit(limit).all()


def update_user(db: Session, db_user: orms.User):
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db.query(orms.User).filter(orms.User.id == user_id).delete()
    db.commit()
    return


### BILLS ###


def create_bill(db: Session, bill: pydantic_models.BillCreate):
    db_bill = orms.Bill(
        legiscanID=bill.legiscanID,
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
    return db.query(orms.Bill).filter(orms.Bill.id == bill_id).first()


def get_bills(db: Session, skip: int = 0, limit: int = 10):
    return db.query(orms.Bill).offset(skip).limit(limit).all()


def get_bill_by_legiscanID(db: Session, legiscan_id: int):
    return db.query(orms.Bill).filter(orms.Bill.legiscanID == legiscan_id).first()


def update_bill(db: Session, db_bill: orms.Bill):
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill


def delete_bill(db: Session, bill_id: int):
    return db.query(models.Bill).filter(models.Bill.id == bill_id).delete()





# ### LEGISLATORS ###


def create_legislator(db: Session, legislator: pydantic_models.LegislatorCreate):
    db_legislator = orms.Legislator(
        chamber=legislator.chamber,
        district=legislator.district,
        email=legislator.email,
        facebook=legislator.facebook,
        imageUrl=legislator.imageUrl,
        instagram=legislator.instagram,
        name=legislator.name,
        office=legislator.office,
        party=legislator.party,
        phone=legislator.phone,
        state=legislator.state,
        #        topIssues=legislator.topIssues,
        twitter=legislator.twitter,
    )
    db.add(db_legislator)
    db.commit()
    db.refresh(db_legislator)
    return db_legislator


def get_legislator(db: Session, legislator_id: int):
    return db.query(orms.Legislator).filter(orms.Legislator.id == legislator_id).first()


def get_legislator_by_name_and_state(db: Session, name: str, state: str):
    return db.query(orms.Legislator).filter(orms.Legislator.name == name, orms.Legislator.state == state).first()


def get_legislators(db: Session, skip: int = 0, limit: int = 10):
    return db.query(orms.Legislator).offset(skip).limit(limit).all()


def update_legislator(db: Session, db_legislator: orms.Legislator):
    db.add(db_legislator)
    db.commit()
    db.refresh(db_legislator)
    return db_legislator


def delete_legislator(db: Session, legislator_id: int):
    db.query(orms.Legislator).filter(orms.Legislator.id == legislator_id).delete()
    db.commit()
    return
