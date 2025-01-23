from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from models import Base
DATABASE_URL = "sqlite:///ride_db.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """
    Функция для инициализации базы данных и создания всех таблиц.
    """
    try:
        Base.metadata.create_all(engine)
    except OperationalError as e:
        print(f"Ошибка при подключении к базе данных: {e}")