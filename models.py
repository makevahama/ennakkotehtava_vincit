from sqlalchemy import Column, String, DateTime
from database import Base


class ReservationDB(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True, index=True)
    room_id = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)