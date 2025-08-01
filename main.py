import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from handlers import router, start_scheduler
from dotenv import load_dotenv
import os
from database import init_db
from sheduler import check_and_update_trips

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def main():
    dp.include_router(router)
    asyncio.create_task(check_and_update_trips())
    await start_scheduler(bot)  # Запускаем планировщик промо-сообщений
    init_db()
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
