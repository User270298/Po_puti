import datetime
import os
import logging
from aiogram import types, F, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from crud import get_user_trips, register_user, create_trip, User
from keyboards import keyboards_main_menu, keyboards_driver, description_choice_keyboard
from database import SessionLocal
from models import Trip
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter

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


@router.chat_member(ChatMemberUpdatedFilter)
async def handle_system_messages(update: ChatMemberUpdated, bot: Bot):
    """
    Удаляет системные сообщения о вступлении или выходе участников.
    """
    try:
        # Проверяем, если пользователь вступил или покинул группу
        if update.new_chat_member.status in ["member"] or update.old_chat_member.status in ["left"]:
            print(f"Удаляем системное сообщение в группе {update.chat.title}")
            await bot.delete_message(chat_id=update.chat.id, message_id=update.message_id)
    except Exception as e:
        print(f"Ошибка удаления сообщения: {e}")


# @router.message(Command(commands=["start"]))
# async def start(message: types.Message):
#     from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
#     # Кнопка с ссылкой на бота
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="🚀 Открыть бота", url="https://t.me/on_the_way_rnd_bot")]
#         ]
#     )
#     # Текст сообщения
#     await message.answer(
#         text=(
#             "👋 Добро пожаловать в группу *По пути!* 🚗\n\n"
#             "Для публикации поездок используйте нашего бота.\nОн поможет вам найти попутчиков и организовать совместные поездки! 🛤️\n\n"
#             "📌 *Что вы можете сделать?*\n"
#             "🚘 Публиковать маршруты для поиска попутчиков\n"
#             "👫 Находить попутчиков для совместных поездок\n"
#             "💰 Экономить на путешествиях, деля расходы\n\n"
#             "🎯 Сделайте свои поездки удобнее и дешевле!"
#         ),
#         parse_mode="Markdown",
#         reply_markup=keyboard
#     )


# Регистрация нового пользователя
@router.message(Command(commands=["start"]))
@db_session
async def start_command(message: types.Message, state: FSMContext, session):
    logger.info(f"Received /start command from user {message.from_user.id}")
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()

    if user:
        logger.info(f"User {message.from_user.id} found in database")
        await message.answer("*Добро пожаловать обратно!*\n\n🚀 Вот ваше главное меню:",
                             parse_mode="Markdown", reply_markup=keyboards_main_menu())
    else:
        logger.info(f"User {message.from_user.id} not found in database, starting registration")
        await message.answer(
            "*Добро пожаловать в Едем вместе Бот!*\n\n"
            "🤖🚘 Этот бот поможет вам найти попутчиков или предложить свои поездки.\n\n"
            "Для публикации поездок необходимо зарегистрироваться. 🚀",
            parse_mode="Markdown"
        )
        await message.answer("📋 *Пожалуйста, отправьте ваше имя для регистрации.*",
                             parse_mode="Markdown")
        await state.set_state(Registration.name)


@router.message(StateFilter(Registration.name))
async def process_name(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered name: {message.text}")
    await state.update_data(name=message.text)
    await message.answer("📧 *Введите ваш email.*", parse_mode="Markdown")
    await state.set_state(Registration.email)


@router.message(StateFilter(Registration.email))
async def process_email(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered email: {message.text}")
    await state.update_data(email=message.text)
    await message.answer("📱 *Введите ваш номер телефона.*", parse_mode="Markdown")
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
    await callback.message.answer("📍 *Введите место, откуда будете выезжать.*", parse_mode="Markdown")
    await state.set_state(Trips.origin)


@router.message(StateFilter(Trips.origin))
async def trip_origin(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered trip origin: {message.text}")
    await state.update_data(origin=message.text)
    await message.answer("🏁 *Введите конечную точку поездки.*", parse_mode="Markdown")
    await state.set_state(Trips.destination)


@router.message(StateFilter(Trips.destination))
async def trip_destination(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered trip destination: {message.text}")
    await state.update_data(destination=message.text)
    await message.answer("📅 *Введите дату и время отправления (в формате ДД.ММ.ГГГГ ЧЧ:ММ).*", parse_mode="Markdown")
    await state.set_state(Trips.departure_time)


@router.message(StateFilter(Trips.departure_time))
async def trip_departure_time(message: types.Message, state: FSMContext):
    try:
        departure_time = datetime.datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        logger.info(f"User {message.from_user.id} entered trip departure time: {message.text}")
        await state.update_data(departure_time=departure_time)
        await message.answer("🪑 *Введите количество доступных мест.*", parse_mode="Markdown")
        await state.set_state(Trips.seats_available)
    except ValueError:
        logger.warning(f"User {message.from_user.id} entered invalid date format: {message.text}")
        await message.answer("❌ *Неверный формат даты. Попробуйте снова (в формате ДД.ММ.ГГГГ ЧЧ:ММ).*",
                             parse_mode="Markdown")


@router.message(StateFilter(Trips.seats_available))
async def trip_seats_available(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ *Пожалуйста, введите корректное число для количества мест.*", parse_mode="Markdown")
        return

    logger.info(f"User {message.from_user.id} entered seats available: {message.text}")
    await state.update_data(seats_available=int(message.text))
    await message.answer("💰 *Введите стоимость за место.*", parse_mode="Markdown")
    await state.set_state(Trips.price_per_seat)





@router.message(StateFilter(Trips.price_per_seat))
async def trip_price_per_seat(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ *Пожалуйста, введите корректное число для стоимости за место.*", parse_mode="Markdown")
        return

    logger.info(f"User {message.from_user.id} entered price per seat: {message.text}")
    await state.update_data(price_per_seat=int(message.text))
    await message.answer(
        "*Хотите дополнительно написать описание?*", parse_mode="Markdown",
        reply_markup=description_choice_keyboard()
    )


@router.callback_query(F.data.startswith("description_"))
async def handle_description_choice(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data.split("_")[1]

    if choice == "yes":
        await callback.message.answer("📝 *Введите описание поездки.*", parse_mode="Markdown")
        await state.set_state(Trips.description)
    else:
        await state.update_data(description=None)
        await trip_description(callback.message, state)


@router.message(StateFilter(Trips.description))
@db_session
async def trip_description(message: types.Message, state: FSMContext, session):
    logger.info(f"User {message.from_user.id} entered description: {message.text}")
    await state.update_data(description=message.text)
    await trip_description(message, state, session)

@router.message(StateFilter(Trips.description))
@db_session
async def trip_description(message: types.Message, state: FSMContext, session):
    data = await state.get_data()
    logger.info(f"User {message.from_user.id} completed trip details: {data}")

    trip = create_trip(
        session,
        user_id=message.from_user.id,
        origin=data['origin'],
        destination=data['destination'],
        departure_time=data['departure_time'],
        seats_available=data['seats_available'],
        price_per_seat=data['price_per_seat'],
        description=message.text
    )

    logger.info(f"Trip created successfully for user {message.from_user.id}")
    await message.answer("Поездка опубликована!", reply_markup=keyboards_main_menu())

    # Получаем количество мест
    seats_available = trip.seats_available

    await message.bot.send_message(
        GROUP_ID,
        f"*Новая поездка!*\n\n"
        f"📍 *Маршрут:* {trip.origin} → {trip.destination}\n"
        f"⏰ *Время отправления:* {trip.departure_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"🪑 *Места:* {seats_available}\n"
        f"💰 *Стоимость за место:* {trip.price_per_seat} рублей\n"
        f"📝*Дополнительно:* {trip.description}",
        parse_mode="Markdown",
        reply_markup=keyboards_driver(trip.user_id, trip.id, seats_available)  # Передаем количество мест
    )
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

    # Проверяем, есть ли места
    if trip.seats_available <= 0:
        await callback.answer("К сожалению, мест больше нет.")
        return

    # Формируем сообщение без изменения количества мест
    seats_available = trip.seats_available

    # Формируем сообщение о поездке
    trip_message = (
        f"📍 *Маршрут:* {trip.origin} → {trip.destination}\n"
        f"⏰ *Время отправления:* {trip.departure_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"🪑 *Места:* {seats_available}\n"
        f"💰 *Стоимость за место:* {trip.price_per_seat} рублей\n"
        f"📝*Дополнительно:* {trip.description}"
    )

    # Формируем кнопку с количеством мест
    button_text = f"Хочу забронировать"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=button_text, callback_data=f"book_trip:{user_id}:{trip_id}")]]
    )

    # Отправляем сообщение пользователю
    await callback.message.answer(trip_message, parse_mode="Markdown", reply_markup=keyboard)

    # Отправляем сообщение водителю
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
    await callback.bot.send_message(chat_id=trip.user_id, text=driver_message, parse_mode="Markdown")

    # Отвечаем пользователю
    await callback.answer("Вы успешно отправили запрос на бронирование водителю.")


# Описание поездки
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
        f"🪑 *Места:* {trip.seats_available}\n"
        f"💰 *Стоимость за место:* {trip.price_per_seat} рублей\n"
        f"💬 *Описание:* {trip.description}\n"
    )

    # Формируем кнопку "Хочу забронировать"
    button_text = f"Хочу забронировать"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=button_text, callback_data=f"book_trip:{callback.from_user.id}:{trip.id}")]]
    )

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

