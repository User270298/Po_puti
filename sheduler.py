import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Trip
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_and_update_trips():
    """
    Функция для проверки поездок и обновления их статуса на "deactive",
    если выполнено условие:
    - Текущее время больше времени отправления + 10 минут.
    """
    while True:
        try:
            with SessionLocal() as session:
                now = datetime.now(timezone.utc).time()  # Получаем текущее время (только время)
                now_datetime = datetime.combine(datetime.today(), now)

                # 2. Добавление 3 часов
                new_datetime = now_datetime + timedelta(hours=3)

                # 3. Получение объекта time обратно (без даты)
                new_time = new_datetime.time()
                # Поиск поездок, которые нужно деактивировать по времени
                trips_to_deactivate_by_time = session.query(Trip).filter(
                    Trip.status == 'active'  # Только активные поездки
                ).all()

                for trip in trips_to_deactivate_by_time:
                    # Получаем только время из `departure_time`
                    departure_time = trip.departure_time.time()
                    comparison_time = (datetime.combine(datetime.today(), departure_time) + timedelta(minutes=10)).time()

                    # Сравниваем только время
                    # print(f"Сравниваем: {new_time} > {comparison_time}")
                    if new_time > comparison_time:
                        logger.info(f"Деактивируем поездку {trip.id} по причине истечения времени отправления.")
                        trip.status = 'deactive'

                # Сохранение изменений в базе данных
                session.commit()

        except Exception as e:
            logger.error(f"Ошибка при обновлении поездок: {e}")

        # Задержка между проверками (например, каждые 60 секунд)
        await asyncio.sleep(60)

if __name__ == "__main__":
    logger.info("Запуск планировщика...")
    asyncio.run(check_and_update_trips())
