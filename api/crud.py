from sqlalchemy.orm import Session

from . import models, schemas


### USERS ###

def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
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
    db.add()
    db.commit()
    db.refresh(db_user)
    return db_user
    
    
def delete_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).delete()



### BILLS ###

def create_bill(db: Session, bill: schemas.BillCreate):
    db_bill = models.Bill(
        identifier=bill.identifier,
        title=bill.title,
        description=bill.description,
        state=bill.state,
        body=bill.body,
        session=bill.session,
        briefing=bill.briefing,
        sponsorIds=bill.sponsorIds,
        status=bill.status,
        latestAction=bill.latestAction,
        yesVotes=bill.yesVotes,
        noVotes=bill.noVotes,
        userVote=bill.userVote
#        topics = 
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill

def get_bill(db: Session, bill_id: int):
    return db.query(models.Bill).filter(models.Bill.id == bill_id).first()

def get_bills(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Bill).offset(skip).limit(limit).all()

def get_bill_by_legiscanID(db: Session, legiscan_id: int):
    return db.query(models.Bill).filter(models.Bill.legiscanID == legiscan_id).first()

def get_bill_by_tags():
    pass

def update_bill(db: Session, db_bill: models.Bill):
    db.add()
    db.commit()
    db.refresh(db_bill)
    return db_bill

def delete_bill(db: Session, bill_id: int):
    return db.query(models.Bill).filter(models.Bill.id == bill_id).delete()





# ### LEGISLATORS ###

def create_legislator(db: Session, legislator: schemas.LegislatorCreate):
    db_legislator = models.Legislator(

        chamber=legislator.chamber,
        district=legislator.district,
        email=legislator.email,
        facebook=legislator.facebook,
#        fundingRecord=legislator.fundingRecord,
        imageUrl=legislator.imageUrl,
        instagram=legislator.instagram,
        name=legislator.name,
        office=legislator.office,
        party=legislator.party,
        phone=legislator.phone,
        state=legislator.state,
#        topIssues=legislator.topIssues,
        twitter=legislator.twitter
    )
    db.add(db_legislator)
    db.commit()
    db.refresh(db_legislator)
    return db_legislator

def get_legislator(db: Session, legislator_id: int):
    return db.query(models.Legislator).filter(models.Legislator.id == legislator_id).first()

def get_legislator_by_name(db: Session, name: int):
    return db.query(models.Legislator).filter(models.Legislator.name == name).first()

def get_legislators(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Legislator).offset(skip).limit(limit).all()

def get_legislator_by_tags():
    pass

def update_legislator(db: Session, db_legislator: models.Legislator):
    db.add()
    db.commit()
    db.refresh(db_legislator)
    return db_legislator

def delete_legislator(db: Session, legislator_id: int):
    return db.query(models.Legislator).filter(models.Legislator.id == legislator_id).delete()