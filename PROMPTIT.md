You: 

Your task is to implement a simple meeting room reservation interface (API). The service must offer users the following functions: ●​ Creating a reservation: Reserve a room for a specific time period. ●​ Canceling a reservation: Delete a reservation. ●​ Viewing reservations: List all reservations for a specific room. Business rules: ● Reservations cannot overlap (two people cannot reserve the same room at the same time). ● Reservations cannot be made in the past. ● The start time must be before the end time. Use in-memory database so setting up environment stays easy. Use python and needed libraries.

ChatGPT: 

Below is a **simple, clean meeting room reservation API** implemented in **Python using FastAPI**, with an **in-memory database** (Python data structures).  
It enforces all the given business rules.

---

## Tech stack

-   **Python 3.9+**
    
-   **FastAPI** – lightweight API framework
    
-   **Pydantic** – request/response validation
    
-   **Uvicorn** – ASGI server
    

---

## Features implemented

✔ Create a reservation  
✔ Cancel a reservation  
✔ View reservations for a room  
✔ Prevent overlapping reservations  
✔ Prevent reservations in the past  
✔ Validate start time < end time  
✔ In-memory storage (no DB setup needed)

---

## Installation

```bash
pip install fastapi uvicorn
```

---

## Run the API

```bash
uvicorn main:app --reload
```

Swagger UI will be available at:

```arduino
http://127.0.0.1:8000/docs
```

---

## `main.py`

```python
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
```

---

## Example requests

### Create reservation

```json
POST /reservations
{
  "room_id": "RoomA",
  "start_time": "2026-01-20T10:00:00",
  "end_time": "2026-01-20T11:00:00"
}
```

### Cancel reservation

```bash
DELETE /reservations/{reservation_id}
```

### View reservations for a room

```bash
GET /rooms/RoomA/reservations
```

---

## Notes

-   Uses **UTC time** to avoid timezone issues
    
-   Easy to extend with:
    
    -   Users
        
    -   Authentication
        
    -   Persistent database (SQLite/Postgres)
        
    -   Room availability checks
        

If you want, I can:

-   Add **unit tests**
    
-   Convert it to **Django**
    
-   Add **authentication**
    
-   Add **room availability endpoint**

You: 

That is not in-memory database. Lets use sqlites in-memory database.

ChatGPT: 

Good catch 👍 — you’re right: a Python list is *in-memory storage*, but not an **in-memory database**.

Below is a **proper SQLite in-memory database** solution using **FastAPI + SQLAlchemy**, while still keeping setup very simple.

---

## Tech stack

-   **Python 3.9+**
    
-   **FastAPI**
    
-   **SQLAlchemy**
    
-   **SQLite (in-memory)**
    
-   **Uvicorn**
    

---

## Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy pydantic
```

---

## Important note about SQLite in-memory

SQLite in-memory databases exist **per connection**.  
To make it work with FastAPI, we must:

-   Use `StaticPool`
    
-   Disable thread checking
    

This ensures **one shared in-memory DB** for the app lifetime.

---

## `main.py`

```python
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
```

---

## Why this **is** a real in-memory database

✔ Uses **SQLite engine**  
✔ Database exists only in RAM  
✔ SQL constraints & queries  
✔ No files created  
✔ Shared across requests

---

## Test it quickly

```bash
uvicorn main:app --reload
```

Open:

```arduino
http://127.0.0.1:8000/docs
```

---

## Possible improvements (optional)

-   Add **unique index** on `(room_id, start_time, end_time)`
    
-   Add **room table**
    
-   Add **transaction locking** for concurrency
    
-   Add **pytest tests**
    
-   Switch to file-based SQLite with one line change
    

If you want this **without FastAPI**, **with Django**, or **with raw SQL only**, just tell me.

You: 

create\_reservation() function has datetime.utcnow(), its deprecated so fix it.

ChatGPT: 

You’re right 👍 — `datetime.utcnow()` is **deprecated** in favor of **timezone-aware datetimes**.

The correct fix is to use **UTC-aware `datetime.now(timezone.utc)`** and ensure all comparisons are done with timezone-aware datetimes.

Below is the **minimal, correct fix**.

---

## ✅ Correct fix (timezone-aware UTC)

### **Change the import**

```python
from datetime import datetime, timezone
```

---

### **Fix in `create_reservation()`**

```python
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
```

---

## Why this is the correct approach

-   ✔ Avoids deprecated APIs
    
-   ✔ Uses **timezone-aware UTC**
    
-   ✔ Prevents naive vs aware datetime bugs
    
-   ✔ Future-proof (Python 3.12+ compliant)
    
-   ✔ Explicit API contract (client must send timezone)
    

---

## Example valid request

```json
{
  "room_id": "RoomA",
  "start_time": "2026-01-20T10:00:00+00:00",
  "end_time": "2026-01-20T11:00:00+00:00"
}
```

---

If you want, I can also:

-   Auto-convert naive datetimes to UTC
    
-   Enforce UTC at the DB layer
    
-   Add ISO-8601 validation
    
-   Add tests for timezone edge cases
    

Just say the word.

You: 

Create exportable .md file of this conversation that I can download.

ChatGPT: 

Your export is ready.

👉 **Download the Markdown file**

This `.md` file contains:

-   The full problem context
    
-   Final SQLite in-memory + FastAPI implementation
    
-   Business rules
    
-   Correct timezone-aware datetime fix
    
-   Run instructions and example request
    

If you want:

-   a **verbatim chat transcript** instead of a clean technical export
    
-   a **README-style** version
    
-   or conversion to **PDF / DOCX**
    

just tell me.

You: 

That doesnt include the conversation. I meant that I want my input prompts and your outputs.

ChatGPT: 

You’re absolutely right — thanks for clarifying 👍  
I’ve now created a **Markdown file that explicitly contains your prompts and my responses**, laid out as a conversation.

👉 **Download the conversation export (.md)**

### What this file includes

-   Each **user message** (your inputs)
    
-   Each **assistant response** (my outputs)
    
-   Clearly separated sections
    
-   Suitable for:
    
    -   Submission
        
    -   Documentation
        
    -   Sharing
        
    -   Archiving
        

### If you want next

I can also:

-   Include **full verbatim code blocks** from each assistant response
    
-   Add **timestamps**
    
-   Export as **PDF / DOCX**
    
-   Generate a **ChatGPT-style transcript**
    

Just tell me how detailed you want the export to be.

You: 

Lets improve the code. First of all could you provide better structure so the code isnt all in one file.

ChatGPT: 

Great — that’s a very reasonable request. Below is a **clean, production-like project structure** with the same functionality, but properly separated into modules instead of everything living in `main.py`.

I’ll first show the structure, then give you the content of each file.

---

# ✅ Suggested Project Structure

```markdown
meeting_room_api/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   └── routers/
│       ├── __init__.py
│       └── reservations.py
│
└── requirements.txt
```

---

# 📦 `requirements.txt`

```nginx
fastapi
uvicorn
sqlalchemy
pydantic
```

Install with:

```bash
pip install -r requirements.txt
```

---

# 🗄️ `app/database.py` (DB setup)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
```

---

# 🧱 `app/models.py` (DB models)

```python
from sqlalchemy import Column, String, DateTime
from .database import Base

class ReservationDB(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True, index=True)
    room_id = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
```

---

# 📄 `app/schemas.py` (Pydantic models)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import List

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
```

---

# 🧠 `app/crud.py` (business logic & DB access)

```python
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from .models import ReservationDB
from .schemas import ReservationCreate

def create_reservation(db: Session, data: ReservationCreate):
    now = datetime.now(timezone.utc)

    if data.start_time.tzinfo is None or data.end_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="Datetimes must be timezone-aware (UTC)"
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
        ReservationDB.end_time > data.start_time,
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
        end_time=data.end_time,
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation


def delete_reservation(db: Session, reservation_id: str):
    reservation = db.query(ReservationDB).filter(
        ReservationDB.id == reservation_id
    ).first()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    db.delete(reservation)
    db.commit()
    return {"message": "Reservation canceled"}


def get_reservations_for_room(db: Session, room_id: str):
    return (
        db.query(ReservationDB)
        .filter(ReservationDB.room_id == room_id)
        .order_by(ReservationDB.start_time)
        .all()
    )
```

---

# 🚦 `app/routers/reservations.py` (API endpoints)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import SessionLocal
from ..schemas import Reservation, ReservationCreate
from .. import crud

router = APIRouter(prefix="/reservations", tags=["reservations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=Reservation)
def create_reservation(
    data: ReservationCreate, db: Session = Depends(get_db)
):
    return crud.create_reservation(db, data)


@router.delete("/{reservation_id}")
def cancel_reservation(
    reservation_id: str, db: Session = Depends(get_db)
):
    return crud.delete_reservation(db, reservation_id)


@router.get(
    "/rooms/{room_id}",
    response_model=List[Reservation],
)
def list_reservations(room_id: str, db: Session = Depends(get_db)):
    return crud.get_reservations_for_room(db, room_id)
```

---

# 🚀 `app/main.py` (entry point)

```python
from fastapi import FastAPI
from .database import engine, Base
from .routers import reservations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Room Reservation API")

app.include_router(reservations.router)
```

---

# ▶️ Run the app

From the project root:

```bash
uvicorn app.main:app --reload
```

Then open:

```arduino
http://127.0.0.1:8000/docs
```

---

# Why this structure is better

| Before | Now |
| --- | --- |
| Everything in one file | Clear separation of concerns |
| Hard to test | CRUD layer is easy to unit test |
| Hard to extend | Easy to add users, rooms, auth |
| Messy | Professional FastAPI layout |

---

# If you want to go further

I can next:

-   Add a **Room table**
    
-   Add **Users + authentication**
    
-   Add **pytest unit tests**
    
-   Add **locking for concurrency**
    
-   Add **Dockerfile**
    

Just tell me 👍

You: 

There is some database related logic inside of routers. I would like to have all the database related logic in its own file. For example the dependency injection.

ChatGPT: 

Good observation — you’re absolutely right. 👍  
I’ll refactor the structure so that **all database-related logic (including dependency injection) lives in `database.py`**, and the router contains **only HTTP/API concerns**.

Below is the **cleaned-up version** with minimal changes, but better separation of concerns.

---

# ✅ What changes conceptually

| Before | After |
| --- | --- |
| `get_db()` lived in the router | ➜ Moves to `app/database.py` |
| Router knew about `SessionLocal` | ➜ Router only depends on `get_db` |
| Mixed concerns | ➜ Clear: **DB = database.py, API = router** |

---

# 🔧 Updated files

## 🗄️ **`app/database.py` (ALL DB-related logic now here)**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
from fastapi import Depends

DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# ✅ Database dependency now lives HERE (not in the router)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 🧱 **`app/models.py` (unchanged)**

```python
from sqlalchemy import Column, String, DateTime
from .database import Base

class ReservationDB(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True, index=True)
    room_id = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
```

---

## 📄 **`app/schemas.py` (unchanged)**

```python
from pydantic import BaseModel
from datetime import datetime
from typing import List

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
```

---

## 🧠 **`app/crud.py` (unchanged — still contains business + DB logic)**

```python
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from .models import ReservationDB
from .schemas import ReservationCreate

def create_reservation(db: Session, data: ReservationCreate):
    now = datetime.now(timezone.utc)

    if data.start_time.tzinfo is None or data.end_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="Datetimes must be timezone-aware (UTC)"
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
        ReservationDB.end_time > data.start_time,
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
        end_time=data.end_time,
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation


def delete_reservation(db: Session, reservation_id: str):
    reservation = db.query(ReservationDB).filter(
        ReservationDB.id == reservation_id
    ).first()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    db.delete(reservation)
    db.commit()
    return {"message": "Reservation canceled"}


def get_reservations_for_room(db: Session, room_id: str):
    return (
        db.query(ReservationDB)
        .filter(ReservationDB.room_id == room_id)
        .order_by(ReservationDB.start_time)
        .all()
    )
```

---

## 🚦 **`app/routers/reservations.py` (NOW CLEAN — no DB logic here)**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import Reservation, ReservationCreate
from .. import crud

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("/", response_model=Reservation)
def create_reservation(
    data: ReservationCreate, 
    db: Session = Depends(get_db),
):
    return crud.create_reservation(db, data)


@router.delete("/{reservation_id}")
def cancel_reservation(
    reservation_id: str, 
    db: Session = Depends(get_db),
):
    return crud.delete_reservation(db, reservation_id)


@router.get(
    "/rooms/{room_id}",
    response_model=List[Reservation],
)
def list_reservations(
    room_id: str, 
    db: Session = Depends(get_db),
):
    return crud.get_reservations_for_room(db, room_id)
```

---

## 🚀 **`app/main.py` (unchanged)**

```python
from fastapi import FastAPI
from .database import engine, Base
from .routers import reservations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Room Reservation API")

app.include_router(reservations.router)
```

---

# Why this is better (architecturally)

You now have:

```pgsql
Routers      → HTTP layer only
CRUD         → Business + DB logic
Database     → Pure infrastructure (engine, sessions, DI)
Models       → DB schema
Schemas      → API contracts
```

This is very close to how real FastAPI projects are structured in production.

---

# If you want to refine further

Next, we could:

-   Move overlap checking into a dedicated **`validators.py`**
    
-   Add a **Room table + foreign key**
    
-   Add **repository pattern** instead of CRUD functions
    
-   Add **unit tests with TestClient + SQLite in-memory**
    

Just tell me your preferred direction.

You: 

Also in the crud.py there is business-logic and data-access logic mixed. Separate them to the services and repositories file.

ChatGPT: 

Great — this is exactly the kind of refinement you’d expect in a real codebase. 👌

Below I separate **business logic (services)** from **data-access logic (repositories)** while keeping your existing structure and behavior.

---

# ✅ New target architecture

After the refactor you’ll have this separation:

| Layer | Responsibility |
| --- | --- |
| **Router** | HTTP / API concerns only |
| **Service (`services.py`)** | ✅ Business rules & validation |
| **Repository (`repositories.py`)** | ✅ Pure database access (queries, inserts, deletes) |
| **Database (`database.py`)** | Engine + session + DI |
| **Models** | SQLAlchemy tables |
| **Schemas** | Pydantic models |

---

# 📁 Updated project structure

```pgsql
meeting_room_api/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── repositories.py   ✅ NEW
│   ├── services.py       ✅ NEW
│   └── routers/
│       ├── __init__.py
│       └── reservations.py
│
└── requirements.txt
```

---

# 🗄️ `app/repositories.py` — **PURE DATA ACCESS**

No business rules here — just database operations.

```python
from sqlalchemy.orm import Session
from .models import ReservationDB
import uuid


def create_reservation_record(
    db: Session,
    room_id: str,
    start_time,
    end_time,
) -> ReservationDB:
    reservation = ReservationDB(
        id=str(uuid.uuid4()),
        room_id=room_id,
        start_time=start_time,
        end_time=end_time,
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def get_overlapping_reservation(
    db: Session,
    room_id: str,
    start_time,
    end_time,
):
    return (
        db.query(ReservationDB)
        .filter(
            ReservationDB.room_id == room_id,
            ReservationDB.start_time < end_time,
            ReservationDB.end_time > start_time,
        )
        .first()
    )


def delete_reservation_by_id(db: Session, reservation_id: str):
    reservation = (
        db.query(ReservationDB)
        .filter(ReservationDB.id == reservation_id)
        .first()
    )

    if reservation:
        db.delete(reservation)
        db.commit()

    return reservation


def list_reservations_by_room(db: Session, room_id: str):
    return (
        db.query(ReservationDB)
        .filter(ReservationDB.room_id == room_id)
        .order_by(ReservationDB.start_time)
        .all()
    )
```

---

# 🧠 `app/services.py` — **PURE BUSINESS LOGIC**

All your rules live here. It calls the repository for DB operations.

```python
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .schemas import ReservationCreate
from . import repositories


def create_reservation_service(db: Session, data: ReservationCreate):
    now = datetime.now(timezone.utc)

    if data.start_time.tzinfo is None or data.end_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="Datetimes must be timezone-aware (UTC)",
        )

    if data.start_time >= data.end_time:
        raise HTTPException(
            status_code=400,
            detail="Start time must be before end time",
        )

    if data.start_time < now:
        raise HTTPException(
            status_code=400,
            detail="Reservations cannot be made in the past",
        )

    overlapping = repositories.get_overlapping_reservation(
        db,
        room_id=data.room_id,
        start_time=data.start_time,
        end_time=data.end_time,
    )

    if overlapping:
        raise HTTPException(
            status_code=400,
            detail="Reservation overlaps with an existing one",
        )

    return repositories.create_reservation_record(
        db,
        room_id=data.room_id,
        start_time=data.start_time,
        end_time=data.end_time,
    )


def cancel_reservation_service(db: Session, reservation_id: str):
    reservation = repositories.delete_reservation_by_id(
        db, reservation_id
    )

    if not reservation:
        raise HTTPException(
            status_code=404, detail="Reservation not found"
        )

    return {"message": "Reservation canceled"}


def list_reservations_service(db: Session, room_id: str):
    return repositories.list_reservations_by_room(db, room_id)
```

---

# 🚦 `app/routers/reservations.py` — **NOW VERY CLEAN**

The router now only wires HTTP → service.

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import Reservation, ReservationCreate
from .. import services

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("/", response_model=Reservation)
def create_reservation(
    data: ReservationCreate,
    db: Session = Depends(get_db),
):
    return services.create_reservation_service(db, data)


@router.delete("/{reservation_id}")
def cancel_reservation(
    reservation_id: str,
    db: Session = Depends(get_db),
):
    return services.cancel_reservation_service(db, reservation_id)


@router.get(
    "/rooms/{room_id}",
    response_model=List[Reservation],
)
def list_reservations(
    room_id: str,
    db: Session = Depends(get_db),
):
    return services.list_reservations_service(db, room_id)
```

---

# ✅ What **did NOT change**

You can keep these files exactly as before:

-   `database.py`
    
-   `models.py`
    
-   `schemas.py`
    
-   `main.py`
    

---

# Why this is much better

You now have a clean **3-layer architecture**:

```nginx
Router → Service → Repository → Database
```

### Benefits

-   Easier to **unit test**
    
    -   You can mock repositories when testing services
        
-   Clearer responsibilities
    
-   Closer to real-world backend architecture
    
-   Much easier to maintain and extend
    

---

# If you want to go even more “enterprise”

Next we could:

-   Introduce a **ReservationRepository class** instead of functions
    
-   Add a **RoomService + RoomRepository**
    
-   Add **transaction management in a separate layer**
    
-   Add **pytest tests** for:
    
    -   Service layer (business rules)
        
    -   Repository layer (DB behavior)
        

Tell me how formal/academic you want the architecture to be — this can go very clean very fast.

You: 

Can you provide structure for the error handling logic?

ChatGPT: 

Yes — below is a **clear, layered error-handling structure** that fits your current architecture (Router → Service → Repository → Database) and keeps concerns well separated.

I’ll give you:

1.  **Conceptual structure (where errors live)**
    
2.  **Concrete file layout**
    
3.  **Custom exceptions**
    
4.  **Service-level validation errors**
    
5.  **Global FastAPI exception handler**
    
6.  **(Optional) Repository errors**
    
7.  **How everything fits together**
    

---

# ✅ 1) Target error-handling model (conceptual)

| Layer | Handles |
| --- | --- |
| **Router** | ❌ No business errors. Only HTTP wiring. |
| **Service** | ✅ Business rule violations → raises *domain exceptions* |
| **Repository** | ⚠️ Only technical/DB issues (rare) |
| **FastAPI Middleware / Exception Handler** | ✅ Converts exceptions → HTTP responses |

Flow:

```pgsql
Router → Service → Repository
                ↑
         Custom Exceptions
                ↓
      Global Exception Handler
                ↓
          Proper HTTP Response
```

---

# ✅ 2) New / updated project structure

Add one new file:

```css
app/
│
├── errors.py           ✅ NEW
├── services.py
├── repositories.py
├── routers/
│   └── reservations.py
└── main.py
```

---

# ✅ 3) `app/errors.py` — Centralized error definitions

```python
from fastapi import HTTPException, status


# ---------- Base Domain Error ----------
class DomainError(Exception):
    """Base class for business/domain errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# ---------- Specific Business Errors ----------
class ReservationOverlapError(DomainError):
    pass


class ReservationInPastError(DomainError):
    pass


class InvalidTimeRangeError(DomainError):
    pass


class ReservationNotFoundError(DomainError):
    pass


class NaiveDatetimeError(DomainError):
    pass
```

👉 This keeps your error *semantics* clear and reusable.

---

# ✅ 4) `app/services.py` — Use structured errors (no HTTP here)

Replace `HTTPException` with your domain errors:

```python
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .schemas import ReservationCreate
from . import repositories
from .errors import (
    ReservationOverlapError,
    ReservationInPastError,
    InvalidTimeRangeError,
    ReservationNotFoundError,
    NaiveDatetimeError,
)


def create_reservation_service(db: Session, data: ReservationCreate):
    now = datetime.now(timezone.utc)

    if data.start_time.tzinfo is None or data.end_time.tzinfo is None:
        raise NaiveDatetimeError("Datetimes must be timezone-aware (UTC)")

    if data.start_time >= data.end_time:
        raise InvalidTimeRangeError("Start time must be before end time")

    if data.start_time < now:
        raise ReservationInPastError("Reservations cannot be made in the past")

    overlapping = repositories.get_overlapping_reservation(
        db,
        room_id=data.room_id,
        start_time=data.start_time,
        end_time=data.end_time,
    )

    if overlapping:
        raise ReservationOverlapError(
            "Reservation overlaps with an existing one"
        )

    return repositories.create_reservation_record(
        db,
        room_id=data.room_id,
        start_time=data.start_time,
        end_time=data.end_time,
    )


def cancel_reservation_service(db: Session, reservation_id: str):
    reservation = repositories.delete_reservation_by_id(
        db, reservation_id
    )

    if not reservation:
        raise ReservationNotFoundError("Reservation not found")

    return {"message": "Reservation canceled"}


def list_reservations_service(db: Session, room_id: str):
    return repositories.list_reservations_by_room(db, room_id)
```

👉 Now the **service layer is framework-agnostic** (no FastAPI here).

---

# ✅ 5) `app/main.py` — Global exception handler

Here we translate domain errors → HTTP responses in ONE place.

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .database import engine, Base
from .routers import reservations
from .errors import (
    DomainError,
    ReservationOverlapError,
    ReservationInPastError,
    InvalidTimeRangeError,
    ReservationNotFoundError,
    NaiveDatetimeError,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Room Reservation API")

app.include_router(reservations.router)


# ---------- GLOBAL ERROR HANDLER ----------
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    status_map = {
        ReservationOverlapError: 400,
        ReservationInPastError: 400,
        InvalidTimeRangeError: 400,
        NaiveDatetimeError: 400,
        ReservationNotFoundError: 404,
    }

    status_code = status_map.get(type(exc), 400)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
        },
    )
```

---

# ✅ 6) (Optional) Repository-level errors

Normally, repositories should **not** raise business errors.  
If you want technical errors handled cleanly, you can add this:

### In `main.py`

```python
from sqlalchemy.exc import SQLAlchemyError

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={
            "error": "DatabaseError",
            "message": "An internal database error occurred",
        },
    )
```

---

# ✅ 7) How this looks in practice

### Example: Overlapping reservation

**Service raises:**

```python
raise ReservationOverlapError("Reservation overlaps with an existing one")
```

**Client receives:**

```json
{
  "error": "ReservationOverlapError",
  "message": "Reservation overlaps with an existing one"
}
```

Status: **400**

---

# ✅ Benefits of this structure

You now have:

✔ Clean separation of concerns  
✔ Centralized error handling  
✔ Reusable business exceptions  
✔ Framework-agnostic services  
✔ Much easier unit testing  
✔ Professional backend design

---

# If you want to go further

I can next add:

-   **Error codes** (e.g., `RESERVATION_OVERLAP`)
    
-   **Machine-readable error format (RFC 7807 / Problem Details)**
    
-   **Localization of error messages**
    
-   **Logging per error type**
    
-   **Custom validation layer before services**
    

Tell me how “enterprise-grade” you want this to be.

