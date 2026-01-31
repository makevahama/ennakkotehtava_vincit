from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import List
from sqlalchemy import (
    create_engine, Column, String, DateTime
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
import uuid

# ----------------------
# Database setup
# ----------------------
DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ReservationDB(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True, index=True)
    room_id = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)


Base.metadata.create_all(bind=engine)

# ----------------------
# FastAPI app
# ----------------------
app = FastAPI(title="Meeting Room Reservation API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------
# Schemas
# ----------------------
class ReservationCreate(BaseModel):
    room_id: str
    start_time: datetime
    end_time: datetime


class Reservation(BaseModel):
    id: str
    room_id: str
    start_time: datetime
    end_time: datetime

    class Config:
        orm_mode = True

# ----------------------
# Endpoints
# ----------------------
@app.post("/reservations", response_model=Reservation)
def create_reservation(
    data: ReservationCreate,
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)

    if data.start_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="start_time must be timezone-aware (UTC)"
        )

    if data.end_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="end_time must be timezone-aware (UTC)"
        )

    if data.start_time >= data.end_time:
        raise HTTPException(
            status_code=400,
            detail="Start time must be before end time"
        )

    if data.start_time < now:
        raise HTTPException(
            status_code=400,
            detail="Reservations cannot be made in the past"
        )

    overlapping = db.query(ReservationDB).filter(
        ReservationDB.room_id == data.room_id,
        ReservationDB.start_time < data.end_time,
        ReservationDB.end_time > data.start_time
    ).first()

    if overlapping:
        raise HTTPException(
            status_code=400,
            detail="Reservation overlaps with an existing one"
        )

    reservation = ReservationDB(
        id=str(uuid.uuid4()),
        room_id=data.room_id,
        start_time=data.start_time,
        end_time=data.end_time
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation



@app.delete("/reservations/{reservation_id}")
def cancel_reservation(
    reservation_id: str,
    db: Session = Depends(get_db)
):
    reservation = db.query(ReservationDB).filter(
        ReservationDB.id == reservation_id
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found"
        )

    db.delete(reservation)
    db.commit()
    return {"message": "Reservation canceled"}


@app.get(
    "/rooms/{room_id}/reservations",
    response_model=List[Reservation]
)
def list_reservations(
    room_id: str,
    db: Session = Depends(get_db)
):
    return db.query(ReservationDB).filter(
        ReservationDB.room_id == room_id
    ).order_by(ReservationDB.start_time).all()
