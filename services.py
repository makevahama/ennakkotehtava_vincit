from datetime import datetime, timezone
from typing import List
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories import ReservationRepository
from schemas import ReservationCreate, Reservation
from models import ReservationDB


class ReservationService:

    def __init__(self, db: Session):
        self.repository = ReservationRepository(db)

    def _validate_timezone_aware(self, dt: datetime, field_name: str) -> None:
        if dt.tzinfo is None:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} must be timezone-aware (UTC)"
            )

    def _validate_time_range(self, start_time: datetime, end_time: datetime) -> None:
        if start_time >= end_time:
            raise HTTPException(
                status_code=400,
                detail="Start time must be before end time"
            )

    def _validate_not_in_past(self, start_time: datetime) -> None:
        now = datetime.now(timezone.utc)
        if start_time < now:
            raise HTTPException(
                status_code=400,
                detail="Reservations cannot be made in the past"
            )

    def _check_overlap(
        self,
        room_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> None:
        overlapping = self.repository.find_overlapping(room_id, start_time, end_time)
        if overlapping:
            raise HTTPException(
                status_code=400,
                detail="Reservation overlaps with an existing one"
            )

    def create_reservation(self, data: ReservationCreate) -> ReservationDB:
        self._validate_timezone_aware(data.start_time, "start_time")
        self._validate_timezone_aware(data.end_time, "end_time")
        self._validate_time_range(data.start_time, data.end_time)
        self._validate_not_in_past(data.start_time)
        self._check_overlap(data.room_id, data.start_time, data.end_time)

        reservation_data = {
            "id": str(uuid.uuid4()),
            "room_id": data.room_id,
            "start_time": data.start_time,
            "end_time": data.end_time
        }

        return self.repository.create(reservation_data)

    def cancel_reservation(self, reservation_id: str) -> dict:
        reservation = self.repository.find_by_id(reservation_id)
        
        if not reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )

        self.repository.delete(reservation)
        return {"message": "Reservation canceled"}

    def get_reservations_for_room(self, room_id: str) -> List[ReservationDB]:
        return self.repository.find_by_room_id(room_id)