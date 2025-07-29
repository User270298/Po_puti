from sqlalchemy.orm import Session
from datetime import datetime, time
from models import User, Trip, TripBooking
# import datetime



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
                seats_available: int = None, price_per_seat: int = None, status: str = 'active', description: str = None):
    # departure_time теперь уже является datetime объектом

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

    # Update last_trip_id for the user
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        user.last_trip_id = trip.id
        session.commit()

    return trip


def get_last_trip(session: Session, user_id: int):
    user = session.query(User).filter(User.id == user_id).first()
    if user and user.last_trip_id:
        return session.query(Trip).filter(Trip.id == user.last_trip_id).first()
    return None


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


def get_users_who_booked_trip(session: Session, trip_id: int):
    """
    Получение пользователей, которые забронировали места на поездку.
    """
    return session.query(User).join(TripBooking).filter(TripBooking.trip_id == trip_id).all()

def book_trip_in_db(session: Session, user_id: int, trip_id: int):
    """
    Создание записи о бронировании поездки пользователем.
    """
    existing_booking = session.query(TripBooking).filter_by(user_id=user_id, trip_id=trip_id).first()
    if existing_booking:
        raise ValueError("Пользователь уже забронировал эту поездку.")

    booking = TripBooking(user_id=user_id, trip_id=trip_id)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking
