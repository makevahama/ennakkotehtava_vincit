from pydantic import BaseModel
from datetime import datetime


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