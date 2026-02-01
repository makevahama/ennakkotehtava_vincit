from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from models import ReservationDB


class ReservationRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, reservation_data: dict) -> ReservationDB:
        reservation = ReservationDB(**reservation_data)
        self.db.add(reservation)
        self.db.commit()
        self.db.refresh(reservation)
        return reservation

    def find_by_id(self, reservation_id: str) -> Optional[ReservationDB]:
        return self.db.query(ReservationDB).filter(
            ReservationDB.id == reservation_id
        ).first()

    def delete(self, reservation: ReservationDB) -> None:
        self.db.delete(reservation)
        self.db.commit()

    def find_by_room_id(self, room_id: str) -> List[ReservationDB]:
        return self.db.query(ReservationDB).filter(
            ReservationDB.room_id == room_id
        ).order_by(ReservationDB.start_time).all()

    def find_overlapping(
        self,
        room_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[ReservationDB]:
        return self.db.query(ReservationDB).filter(
            ReservationDB.room_id == room_id,
            ReservationDB.start_time < end_time,
            ReservationDB.end_time > start_time
        ).first()