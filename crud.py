from sqlalchemy.orm import Session
from datetime import datetime
from models import User, Trip


def register_user(session: Session, telegram_id: int, name: str, email: str, phone: str):
    """
    Регистрация нового пользователя.
    """
    if not telegram_id or not name or not phone:
        raise ValueError("Недостаточно данных для регистрации пользователя.")

    user = User(telegram_id=telegram_id, name=name, email=email, phone=phone)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_trip(session: Session, user_id: int, origin: str, destination: str, departure_time: datetime,
                seats_available: int, price_per_seat: int, status: str = 'active', description: str = None):
    """
    Создание новой поездки.
    """
    if not user_id or not origin or not destination or not departure_time or seats_available <= 0 or price_per_seat <= 0:
        raise ValueError("Недостаточно данных для создания поездки.")

    trip = Trip(
        user_id=user_id,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        seats_available=seats_available,
        price_per_seat=price_per_seat,
        status=status,
        description=description
    )
    session.add(trip)
    session.commit()
    session.refresh(trip)
    return trip


def get_all_trips(session: Session):
    """
    Получение всех поездок.
    """
    return session.query(Trip).all()


def get_user_trips(session: Session, user_id: int):
    """
    Получение всех поездок конкретного пользователя.
    """
    return session.query(Trip).filter(Trip.user_id == user_id).all()


def get_all_users(session: Session):
    """
    Получение всех пользователей.
    """
    return session.query(User).all()
