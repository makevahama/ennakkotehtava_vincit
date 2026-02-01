from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas import ReservationCreate, Reservation
from services import ReservationService

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", response_model=Reservation)
def create_reservation(
    data: ReservationCreate,
    db: Session = Depends(get_db)
):
    """Create a new reservation"""
    service = ReservationService(db)
    return service.create_reservation(data)


@router.delete("/{reservation_id}")
def cancel_reservation(
    reservation_id: str,
    db: Session = Depends(get_db)
):
    """Cancel an existing reservation"""
    service = ReservationService(db)
    return service.cancel_reservation(reservation_id)


@router.get("/rooms/{room_id}", response_model=List[Reservation])
def list_reservations(
    room_id: str,
    db: Session = Depends(get_db)
):
    """Get all reservations for a specific room"""
    service = ReservationService(db)
    return service.get_reservations_for_room(room_id)