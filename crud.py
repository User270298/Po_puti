from sqlalchemy.orm import Session
from datetime import datetime, time
from models import User, Trip
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


def create_trip(session: Session, user_id: int, origin: str, destination: str, departure_time: time,
                seats_available: int, price_per_seat: int, status: str = 'active', description: str = None):
    # Ensure `departure_time` is a full datetime object
    departure_time = datetime.combine(datetime.utcnow().date(), departure_time)

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
