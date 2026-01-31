# Conversation Export – Meeting Room Reservation API

---

## User
Your task is to implement a simple meeting room reservation interface (API).
The service must offer users the following functions:
- Creating a reservation
- Canceling a reservation
- Viewing reservations

Business rules:
- No overlapping reservations
- No reservations in the past
- Start time must be before end time

Use in-memory database.
Use python and needed libraries.

---

## Assistant
Below is a simple, clean meeting room reservation API implemented in Python using FastAPI, with an in-memory database (Python data structures).
It enforces all the given business rules.

Tech stack

Python 3.9+

FastAPI – lightweight API framework

Pydantic – request/response validation

Uvicorn – ASGI server

Features implemented

✔ Create a reservation
✔ Cancel a reservation
✔ View reservations for a room
✔ Prevent overlapping reservations
✔ Prevent reservations in the past
✔ Validate start time < end time
✔ In-memory storage (no DB setup needed)

Installation
pip install fastapi uvicorn

Run the API
uvicorn main:app --reload


Swagger UI will be available at:

http://127.0.0.1:8000/docs

main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
import uuid

app = FastAPI(title="Meeting Room Reservation API")

# In-memory database
reservations = []


class ReservationCreate(BaseModel):
    room_id: str
    start_time: datetime
    end_time: datetime


class Reservation(BaseModel):
    id: str
    room_id: str
    start_time: datetime
    end_time: datetime


def is_overlapping(room_id: str, start: datetime, end: datetime) -> bool:
    for r in reservations:
        if r["room_id"] == room_id:
            if start < r["end_time"] and end > r["start_time"]:
                return True
    return False


@app.post("/reservations", response_model=Reservation)
def create_reservation(data: ReservationCreate):
    now = datetime.utcnow()

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

    if is_overlapping(data.room_id, data.start_time, data.end_time):
        raise HTTPException(
            status_code=400,
            detail="Reservation overlaps with an existing one"
        )

    reservation = {
        "id": str(uuid.uuid4()),
        "room_id": data.room_id,
        "start_time": data.start_time,
        "end_time": data.end_time,
    }

    reservations.append(reservation)
    return reservation


@app.delete("/reservations/{reservation_id}")
def cancel_reservation(reservation_id: str):
    for r in reservations:
        if r["id"] == reservation_id:
            reservations.remove(r)
            return {"message": "Reservation canceled"}

    raise HTTPException(
        status_code=404,
        detail="Reservation not found"
    )


@app.get("/rooms/{room_id}/reservations", response_model=List[Reservation])
def get_reservations_for_room(room_id: str):
    return [
        r for r in reservations
        if r["room_id"] == room_id
    ]


Example requests
Create reservation
POST /reservations
{
  "room_id": "RoomA",
  "start_time": "2026-01-20T10:00:00",
  "end_time": "2026-01-20T11:00:00"
}

Cancel reservation
DELETE /reservations/{reservation_id}
View reservations for a room
GET /rooms/RoomA/reservations

Notes

Uses UTC time to avoid timezone issues

Easy to extend with:

Users

Authentication

Persistent database (SQLite/Postgres)

Room availability checks

If you want, I can:

Add unit tests

Convert it to Django

Add authentication

Add room availability endpoint
---

## User
That is not in-memory database. Lets use sqlite in-memory database.

---

## Assistant
Good catch 👍 — you’re right: a Python list is in-memory storage, but not an in-memory database.

Below is a proper SQLite in-memory database solution using FastAPI + SQLAlchemy, while still keeping setup very simple.

Tech stack

Python 3.9+

FastAPI

SQLAlchemy

SQLite (in-memory)

Uvicorn

Install dependencies
pip install fastapi uvicorn sqlalchemy pydantic

Important note about SQLite in-memory

SQLite in-memory databases exist per connection.
To make it work with FastAPI, we must:

Use StaticPool

Disable thread checking

main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
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
    now = datetime.utcnow()

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

    # Overlap check
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

Why this is a real in-memory database

✔ Uses SQLite engine
✔ Database exists only in RAM
✔ SQL constraints & queries
✔ No files created
✔ Shared across requests

Test it quickly
uvicorn main:app --reload


Open:

http://127.0.0.1:8000/docs

Possible improvements (optional)


Add unique index on (room_id, start_time, end_time)


Add room table


Add transaction locking for concurrency


Add pytest tests


Switch to file-based SQLite with one line change


If you want this without FastAPI, with Django, or with raw SQL only, just tell me.
---

## User
create_reservation() function has datetime.utcnow(), its deprecated so fix it.

---

## Assistant
You’re right 👍 — datetime.utcnow() is deprecated in favor of timezone-aware datetimes.

The correct fix is to use UTC-aware datetime.now(timezone.utc) and ensure all comparisons are done with timezone-aware datetimes.

Below is the minimal, correct fix.
✅ Correct fix (timezone-aware UTC)
Change the import
from datetime import datetime, timezone

Fix in create_reservation()

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

Why this is the correct approach


✔ Avoids deprecated APIs


✔ Uses timezone-aware UTC


✔ Prevents naive vs aware datetime bugs


✔ Future-proof (Python 3.12+ compliant)


✔ Explicit API contract (client must send timezone)



Example valid request
{
  "room_id": "RoomA",
  "start_time": "2026-01-20T10:00:00+00:00",
  "end_time": "2026-01-20T11:00:00+00:00"
}


If you want, I can also:


Auto-convert naive datetimes to UTC


Enforce UTC at the DB layer


Add ISO-8601 validation


Add tests for timezone edge cases


Just say the word.


---

## User
Create exportable .md file of this conversation that I can download.

---

## Assistant
Your export is ready.

👉 Download the Markdown file

This .md file contains:

The full problem context

Final SQLite in-memory + FastAPI implementation

Business rules

Correct timezone-aware datetime fix

Run instructions and example request

If you want:

a verbatim chat transcript instead of a clean technical export

a README-style version

or conversion to PDF / DOCX

just tell me.

---

## End of Conversation
