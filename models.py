from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

# Таблица пользователей
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с поездками
    trips = relationship("Trip", back_populates="user", foreign_keys="Trip.user_id")
    booked_trips = relationship("TripBooking", back_populates="user")
# Таблица поездок
class Trip(Base):
    __tablename__ = "trip"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    departure_time = Column(DateTime, nullable=False)
    seats_available = Column(Integer, nullable=False)
    price_per_seat = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="active")
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с пользователем
    user = relationship("User", back_populates="trips", foreign_keys=[user_id])
    booked_users = relationship("TripBooking", back_populates="trip")
class TripBooking(Base):
    __tablename__ = "trip_booking"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trip.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="booked_trips")
    trip = relationship("Trip", back_populates="booked_users")
