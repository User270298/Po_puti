import datetime
import os
import logging
from aiogram import types, F, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from crud import get_user_trips, register_user, create_trip, User, get_last_trip, create_trip, get_users_who_booked_trip, book_trip_in_db
from keyboards import keyboards_main_menu, keyboards_driver, description_choice_keyboard
from database import SessionLocal
from models import Trip
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter
from datetime import datetime, timedelta
import asyncio
import pytz



load_dotenv()
router = Router()

GROUP_ID = os.getenv("GROUP_ID")  # ID группы для публикаций

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from functools import wraps


def db_session(func):
    """
    Асинхронный декоратор для управления сессией базы данных.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        with SessionLocal() as session:
            kwargs['session'] = session
            return await func(*args, **kwargs)

    return wrapper


class Registration(StatesGroup):
    name = State()
    email = State()
    phone = State()
    

class Trips(StatesGroup):
    origin = State()
    destination = State()
    departure_time = State()
    seats_available = State()
    price_per_seat = State()
    description = State()


# @router.chat_member(ChatMemberUpdatedFilter)
# async def handle_system_messages(update: ChatMemberUpdated, bot: Bot):
#     """
#     Удаляет системные сообщения о вступлении или выходе участников.
#     """
#     try:
#         # Проверяем, если пользователь вступил или покинул группу
#         if update.new_chat_member.status in ["member"] or update.old_chat_member.status in ["left"]:
#             print(f"Удаляем системное сообщение в группе {update.chat.title}")
#             await bot.delete_message(chat_id=update.chat.id, message_id=update.message_id)
#     except Exception as e:
#         print(f"Ошибка удаления сообщения: {e}")


# @router.message(Command(commands=["start"]))
# async def start(message: types.Message):
#     from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
#     # Кнопка с ссылкой на бота
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="🚀 Открыть группу", url="https://t.me/num_po_puti")]
#         ]
#     )
#     # Текст сообщения
#     await message.answer(
#         text=(
# '''🚗 Хочешь больше попутчиков? Переходи в новую группу!
# 👋 Ты уже пользуешься нашей группой «Нам по пути» для поездок c Суворовского района и обратно? Отлично!

# 🔹 Встречайте новую группу — «Нам по пути | Все районы»!
# ✅ Больше маршрутов — не только Суворовский, но и любые направления
# ✅ Еще больше водителей и пассажиров — больше шансов найти попутчика
# ✅ Гибкость — поездки между любыми районами без ограничений
# ✅ Телеграм бот - для удобства поиска и публикации маршрутов
# 👉 Переходи и подписывайся: @num_po_puti

# Не ограничивай себя одним районом — путешествуй по всему городу дешево и удобно!'''
#         ),
#         parse_mode="Markdown",
#         reply_markup=keyboard
#     )


# # Регистрация нового пользователя
@router.message(Command(commands=["start"]))
@db_session
async def start_command(message: types.Message, state: FSMContext, session):
    logger.info(f"Received /start command from user {message.from_user.id}")
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()

    if user:
        logger.info(f"User {message.from_user.id} found in database")
        await message.answer("*Добро пожаловать обратно!*\n\n🚀 Главное меню:",
                             parse_mode="Markdown", reply_markup=keyboards_main_menu())
    else:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        logger.info(f"User {message.from_user.id} not found in database, starting registration")
        keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Открыть бота", url="https://t.me/num_po_puti_bot")]
        ]
    )
        await message.answer(
            "*Добро пожаловать в Нам по пути Бот!*\n\n"
            "🤖🚘 Этот бот поможет вам найти попутчиков или предложить свои поездки.\n\n"
            "Для публикации поездок необходимо зарегистрироваться. 🚀",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await message.answer("📋 *Пожалуйста, отправьте ваше имя для регистрации:*",
                             parse_mode="Markdown")
        await state.set_state(Registration.name)


@router.message(StateFilter(Registration.name))
async def process_name(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered name: {message.text}")
    await state.update_data(name=message.text)
    await message.answer("📧 *Введите ваш email:*", parse_mode="Markdown")
    await state.set_state(Registration.email)


@router.message(StateFilter(Registration.email))
async def process_email(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered email: {message.text}")
    await state.update_data(email=message.text)
    await message.answer("📱 *Введите ваш номер телефона:*", parse_mode="Markdown")
    await state.set_state(Registration.phone)


@router.message(StateFilter(Registration.phone))
@db_session
async def process_phone(message: types.Message, state: FSMContext, session):
    logger.info(f"User {message.from_user.id} entered phone: {message.text}")
    data = await state.get_data()
    register_user(session, telegram_id=message.from_user.id, name=data['name'], email=data['email'], phone=message.text)

    logger.info(f"User {message.from_user.id} successfully registered")
    await message.answer("🎉 *Вы успешно зарегистрированы!*", parse_mode="Markdown", reply_markup=keyboards_main_menu())
    await state.clear()


# Публикация поездки
@router.callback_query(F.data == "publish_trip")
async def create_trip_command(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.message.from_user.id} initiated trip creation")
    await callback.message.answer("📍 *Введите место, откуда будете выезжать:*", parse_mode="Markdown")
    await state.set_state(Trips.origin)


@router.message(StateFilter(Trips.origin))
async def trip_origin(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered trip origin: {message.text}")
    await state.update_data(origin=message.text)
    await message.answer("🏁 *Введите конечную точку поездки:*", parse_mode="Markdown")
    await state.set_state(Trips.destination)


@router.message(StateFilter(Trips.destination))
async def trip_destination(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered trip destination: {message.text}")
    await state.update_data(destination=message.text)
    await message.answer("📅 *Время отправления (в формате ЧЧ:ММ, например 15:24):*", parse_mode="Markdown")
    await state.set_state(Trips.departure_time)


@router.message(StateFilter(Trips.departure_time))
async def trip_departure_time(message: types.Message, state: FSMContext):
    try:
        # Парсим введенное время
        departure_time = datetime.strptime(message.text, "%H:%M").time()
        now = datetime.now().time()  # Получаем текущее время

        # Проверяем, что введенное время больше текущего
        if departure_time <= now:
            logger.warning(f"User {message.from_user.id} entered a past or current time: {message.text}")
            await message.answer("❌ *Введенное время должно быть больше текущего. Попробуйте снова:*",
                                 parse_mode="Markdown")
            return

        logger.info(f"User {message.from_user.id} entered trip departure time: {message.text}")
        await state.update_data(departure_time=departure_time)
        await message.answer("🪑 *Введите количество доступных мест:*", parse_mode="Markdown")
        await state.set_state(Trips.seats_available)
    except ValueError:
        logger.warning(f"User {message.from_user.id} entered invalid time format: {message.text}")
        await message.answer("❌ *Неверный формат времени. Попробуйте снова (в формате ЧЧ:ММ).*", parse_mode="Markdown")


@router.message(StateFilter(Trips.seats_available))
async def trip_seats_available(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ *Пожалуйста, введите корректное число для количества мест.*", parse_mode="Markdown")
        return

    logger.info(f"User {message.from_user.id} entered seats available: {message.text}")
    await state.update_data(seats_available=int(message.text))
    await message.answer("💰 *Введите стоимость за место:*", parse_mode="Markdown")
    await state.set_state(Trips.price_per_seat)


@router.message(StateFilter(Trips.price_per_seat))
async def trip_price_per_seat(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ *Пожалуйста, введите корректное число для стоимости за место.*", parse_mode="Markdown")
        return

    logger.info(f"User {message.from_user.id} entered price per seat: {message.text}")
    await state.update_data(price_per_seat=int(message.text))
    await message.answer(
        "*Теперь введите описание поездки(необязательный пункт):*", parse_mode="Markdown"
    )
    await state.set_state(Trips.description)


@router.message(StateFilter(Trips.description))
@db_session
async def finalize_trip_creation(message: types.Message, state: FSMContext, session):
    data = await state.get_data()
    # logger.info(f"User {message.from_user.id} completed trip details: {data}")
    logger.info(f"User {message.from_user.id} entered description: {message.text}")
    description = message.text.strip()
    # Создаем поездку с учетом всех данных, включая описание, если оно есть
    trip = create_trip(
        session,
        user_id=message.from_user.id,
        origin=data['origin'],
        destination=data['destination'],
        departure_time=data['departure_time'],
        seats_available=data['seats_available'],
        price_per_seat=data['price_per_seat'],
        description=description  # если описание None, будет сохранено как None
    )
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    logger.info(f"Trip created successfully for user {message.from_user.id}")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='❌ Отменить поездку', callback_data=f"cancel_trip:{trip.id}")]])
    await message.answer("Если хотите отменить поездку нажмите на кнопку", reply_markup=keyboard)
    await message.answer("Поездка опубликована!", reply_markup=keyboards_main_menu())
    print(f"Регистрация {trip.user_id, trip.id}")

    # Отправляем информацию о поездке в группу
    await message.bot.send_message(
        GROUP_ID,
        f"*Новая поездка!*\n\n"
        f"📍 *Маршрут:* {trip.origin} → {trip.destination}\n"
        f"⏰ *Время отправления:* {trip.departure_time.strftime('%H:%M')}\n"
        f'🪑*Количество мест:* {trip.seats_available}\n"'
        f"💰 *Стоимость за место:* {trip.price_per_seat} рублей\n"
        f"{f'📝*Дополнительно:* {trip.description}' if trip.description else ''}",
        parse_mode="Markdown",
        reply_markup=keyboards_driver(trip.user_id, trip.id)  # Без учета мест
    )

    # Очистить состояние FSM
    await state.clear()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@router.callback_query(F.data.startswith("book_trip:"))
@db_session
async def book_trip(callback: types.CallbackQuery, session):
    # Извлекаем user_id и trip_id из callback_data
    user_id, trip_id = map(int, callback.data.split(":")[1:])

    # Находим поездку в базе данных
    trip = session.query(Trip).filter_by(id=trip_id).first()
    if not trip:
        await callback.answer("Поездка не найдена.")
        return
    print(f"Запрос поездки {trip.user_id, trip.id}")
    book_trip_in_db(session, user_id, trip_id)
    # Отправляем уведомление водителю
    passenger_name = callback.from_user.full_name or "Имя скрыто"
    passenger_username = callback.from_user.username or "Не указано"
    driver_message = (
        f"📬 *Новый запрос на поездку!*\n\n"
        f"👤 *Имя пассажира:* {passenger_name}\n"
        f"📇 *Username:* @{passenger_username}\n"
        f"📍 *Маршрут:* {trip.origin} → {trip.destination}\n"
        f"⏰ *Время отправления:* {trip.departure_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"💬 Напишите пассажиру в личные сообщения для уточнения деталей."
    )

    try:
        await callback.bot.send_message(chat_id=trip.user_id, text=driver_message, parse_mode="Markdown")
        await callback.answer("Вы успешно отправили запрос на бронирование водителю.")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения водителю: {e}")
        await callback.answer("Не удалось отправить запрос водителю. Попробуйте позже.")


@router.callback_query(F.data.startswith("view_trip_"))
@db_session
async def view_trip(callback: types.CallbackQuery, session):
    # Получаем подробности о поездке
    trip_id = int(callback.data.split("_")[2])
    trip = session.query(Trip).filter_by(id=trip_id).first()
    if not trip:
        await callback.answer("Поездка не найдена.")
        return

    # Формируем сообщение о поездке
    trip_message = (
        f"📍 *Маршрут:* {trip.origin} → {trip.destination}\n"
        f"⏰ *Время отправления:* {trip.departure_time.strftime('%d.%m.%Y %H:%M')}\n"
        f'🪑 *Количество мест:* {trip.seats_available}\n"'
        f"💰 *Стоимость за место:* {trip.price_per_seat} рублей\n"
        f"{f'📝*Дополнительно:* {trip.description}' if trip.description else ''}"
    )

    # Формируем кнопку "Хочу забронировать"
    keyboard = keyboards_driver(callback.from_user.id, trip.id)

    # Отправляем сообщение с кнопкой
    await callback.message.answer(trip_message, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data == "search_trips")
@db_session
async def search_trips(callback: types.CallbackQuery, session):
    # Получаем активные поездки
    trips = session.query(Trip).filter_by(status='active').all()

    if not trips:
        await callback.message.answer("📅 Нет активных поездок.")
        return

    # Формируем клавиатуру для активных поездок
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for trip in trips:
        trip_info = f"{trip.origin} → {trip.destination} | {trip.departure_time.strftime('%d.%m.%Y %H:%M')}"
        button = InlineKeyboardButton(text=trip_info, callback_data=f"view_trip_{trip.id}")
        keyboard.inline_keyboard.append([button])

    # Отправляем сообщение с поездками
    await callback.message.answer("📅 *Выберите поездку:*", parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data.startswith("cancel_trip:"))
@db_session
async def cancel_trip(callback: types.CallbackQuery, session):
    trip_id = int(callback.data.split(":")[1])
    trip = session.query(Trip).filter_by(id=trip_id).first()

    if not trip:
        await callback.answer("Поездка не найдена.")
        return

    # Обновляем статус поездки на 'cancelled'
    trip.status = "cancelled"
    session.commit()

    # Удаляем сообщение о поездке из группы
    try:
        await callback.bot.delete_message(chat_id=GROUP_ID, message_id=trip.group_message_id)
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")

    # Отправляем уведомления всем пользователям, которые забронировали места
    booked_users = get_users_who_booked_trip(session, trip_id)  # Функция для получения пользователей, которые забронировали поездку

    for user in booked_users:
        try:
            await callback.bot.send_message(
                user.telegram_id,
                f"🚨 *Внимание!* Поездка {trip.origin} → {trip.destination} отменена.\n"
                f"Причина: {callback.from_user.full_name} отменил(а) поездку.\n"
                f"💡 Пожалуйста, выберите другую поездку или создайте свою!"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю {user.telegram_id}: {e}")

    await callback.answer("Поездка отменена. Все участники были уведомлены.")


async def send_weekly_promo(bot: Bot):
    """
    Отправляет промо-сообщение в группу каждую неделю в понедельник в 10:00
    """
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        # Ждем до следующего понедельника 10:00
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0 and now.hour >= 10:
            days_until_monday = 7
        
        next_monday = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
        wait_seconds = (next_monday - now).total_seconds()
        
        await asyncio.sleep(wait_seconds)
        
        # Отправляем промо-сообщение
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Открыть группу", url="https://t.me/num_po_puti")]
            ]
        )
        
        promo_message = (
            "🚗 Хочешь больше попутчиков? Переходи в новую группу!\n"
            "👋 Ты уже пользуешься нашей группой «Нам по пути» для поездок c Суворовского района и обратно? Отлично!\n\n"
            "🔹 Встречайте новую группу — «Нам по пути | Все районы»!\n"
            "✅ Больше маршрутов — не только Суворовский, но и любые направления\n"
            "✅ Еще больше водителей и пассажиров — больше шансов найти попутчика\n"
            "✅ Гибкость — поездки между любыми районами без ограничений\n"
            "✅ Телеграм бот - для удобства поиска и публикации маршрутов\n"
            "👉 Переходи и подписывайся: @num_po_puti\n\n"
            "Не ограничивай себя одним районом — путешествуй по всему городу дешево и удобно!"
        )
        
        try:
            await bot.send_message(
                chat_id="@suvorovskynam",
                text=promo_message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            logger.info("Weekly promo message sent successfully")
        except Exception as e:
            logger.error(f"Error sending weekly promo message: {e}")

# Добавляем функцию для запуска планировщика
async def start_scheduler(bot: Bot):
    """
    Запускает планировщик отправки промо-сообщений
    """
    asyncio.create_task(send_weekly_promo(bot))
