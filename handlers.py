import datetime
import os
import logging
from aiogram import types, F, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from crud import get_user_trips, register_user, create_trip, User, get_last_trip, create_trip, get_users_who_booked_trip, book_trip_in_db
from keyboards import keyboards_main_menu, keyboards_driver, description_choice_keyboard, skip_description_keyboard, quick_routes_keyboard, quick_time_keyboard
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
GROUP_ID_ALL = os.getenv("GROUP_ID_ALL")
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
    phone = State()
    

class Trips(StatesGroup):
    origin = State()
    destination = State()
    departure_time = State()
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
#             [InlineKeyboardButton(text="🚀 Открыть бота", url="https://t.me/num_po_puti_bot")]
#         ]
#     )
#     promo_message = (
#             "🚗 *Ищешь попутчиков по городу?*\n\n"
#             "👋 Теперь у нас есть *Telegram-бот*! Публикуй маршруты и находи попутчиков в пару кликов.\n\n"
#             "✅ Поездки между любыми районами\n"
#             "✅ Удобный поиск и публикация\n"
#             "✅ Больше маршрутов и больше людей\n\n"
#             "🚀 Нажми на кнопку ниже, чтобы открыть бота!"
#         )
# #     promo_message=('''🚗 Хочешь больше попутчиков? Переходи в новую группу!
# # 👋 Ты уже пользуешься нашей группой «Нам по пути» для поездок c Суворовского района и обратно? Отлично!

# # 🔹 Встречайте новую группу — «Нам по пути | Все районы»!
# # ✅ Больше маршрутов — не только Суворовский, но и любые направления
# # ✅ Еще больше водителей и пассажиров — больше шансов найти попутчика
# # ✅ Гибкость — поездки между любыми районами без ограничений
# # ✅ Телеграм бот - для удобства поиска и публикации маршрутов
# # 👉 Переходи и подписывайся: @num_po_puti

# # Не ограничивай себя одним районом — путешествуй по всему городу дешево и удобно!''')
#     # Текст сообщения
#     await message.answer(
#         text=promo_message,
#         parse_mode="Markdown",
#         reply_markup=keyboard
#     )


# # Регистрация нового пользователя
@router.message(Command(commands=["start"]))
@db_session
async def start_command(message: types.Message, state: FSMContext, session):
    # Проверяем, что команда отправлена в личном чате
    if message.chat.type != "private":
        return
    
    logger.info(f"Received /start command from user {message.from_user.id}")
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()

    if user:
        logger.info(f"User {message.from_user.id} found in database")
        await message.answer("*Добро пожаловать обратно!*\n\n🚀 Главное меню:",
                             parse_mode="Markdown", reply_markup=keyboards_main_menu())
    else:
        logger.info(f"User {message.from_user.id} not found in database, starting registration")
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
        
        # Создаем reply клавиатуру для отправки номера телефона
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            "*Добро пожаловать в Нам по пути Бот!*\n\n"
            "🤖🚘 Этот бот поможет вам найти попутчиков или предложить свои поездки.\n\n"
            "📱 *Для регистрации отправьте ваш номер телефона:*",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await state.set_state(Registration.phone)


@router.message(StateFilter(Registration.phone))
@db_session
async def process_phone(message: types.Message, state: FSMContext, session):
    # Проверяем, что сообщение отправлено в личном чате
    if message.chat.type != "private":
        return
    
    # Проверяем, что это контакт
    if not message.contact:
        await message.answer("❌ Пожалуйста, нажмите кнопку '📱 Отправить номер телефона'")
        return
    
    phone_number = message.contact.phone_number
    user_name = message.contact.first_name or message.from_user.first_name or "Пользователь"
    
    logger.info(f"User {message.from_user.id} sent phone: {phone_number}")
    
    # Регистрируем пользователя
    register_user(
        session, 
        telegram_id=message.from_user.id, 
        name=user_name, 
        email="", 
        phone=phone_number
    )
    
    logger.info(f"User {message.from_user.id} successfully registered")
    
    # Убираем reply клавиатуру
    from aiogram.types import ReplyKeyboardRemove
    
    await message.answer(
        "🎉 *Регистрация завершена!*\n\n"
        "✅ Теперь вы можете публиковать поездки и искать попутчиков.",
        parse_mode="Markdown", 
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("🚀 Главное меню:", reply_markup=keyboards_main_menu())
    await state.clear()





# Публикация поездки
@router.callback_query(F.data == "publish_trip")
async def create_trip_command(callback: types.CallbackQuery, state: FSMContext):
    # Проверяем, что callback отправлен в личном чате
    if callback.message.chat.type != "private":
        await callback.answer("❌ Эта функция доступна только в личных сообщениях с ботом")
        return
    
    logger.info(f"User {callback.message.from_user.id} initiated trip creation")
    await callback.message.answer(
        "🚗 *Создание поездки*\n\n"
        "Выберите популярный маршрут или создайте свой:",
        parse_mode="Markdown",
        reply_markup=quick_routes_keyboard()
    )


@router.callback_query(F.data.startswith("quick_route:"))
async def quick_route_selected(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора быстрого маршрута"""
    # Проверяем, что callback отправлен в личном чате
    if callback.message.chat.type != "private":
        await callback.answer("❌ Эта функция доступна только в личных сообщениях с ботом")
        return
    
    route_data = callback.data.split(":")
    origin_key, destination_key = route_data[1], route_data[2]
    
    # Маппинг ключей на названия
    route_names = {
        "suvorovskiy": "Суворовский район",
        "center": "Центр города",
        "station": "Ростов Главный"
    }
    
    origin = route_names.get(origin_key, origin_key)
    destination = route_names.get(destination_key, destination_key)
    
    await state.update_data(origin=origin, destination=destination)
    
    await callback.message.answer(
        f"📍 *Маршрут:* {origin} → {destination}\n\n"
        "⏰ *Выберите время отправления:*",
        parse_mode="Markdown",
        reply_markup=quick_time_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "custom_route")
async def custom_route_selected(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора пользовательского маршрута"""
    # Проверяем, что callback отправлен в личном чате
    if callback.message.chat.type != "private":
        await callback.answer("❌ Эта функция доступна только в личных сообщениях с ботом")
        return
    
    await callback.message.answer("📍 *Введите место, откуда будете выезжать:*", parse_mode="Markdown")
    await state.set_state(Trips.origin)
    await callback.answer()


@router.callback_query(F.data.startswith("quick_time:"))
async def quick_time_selected(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора быстрого времени"""
    # Проверяем, что callback отправлен в личном чате
    if callback.message.chat.type != "private":
        await callback.answer("❌ Эта функция доступна только в личных сообщениях с ботом")
        return
    
    # Логируем полный callback_data для отладки
    logger.info(f"Full callback_data: {callback.data}")
    
    # Более надежный способ извлечения времени из callback_data
    parts = callback.data.split(":")
    if len(parts) >= 3:
        time_str = f"{parts[1]}:{parts[2]}"
    else:
        time_str = parts[1] if len(parts) > 1 else ""
    
    logger.info(f"Extracted time_str: '{time_str}'")
    
    # Проверяем, что время не пустое
    if not time_str or ":" not in time_str:
        logger.error(f"Invalid time format: '{time_str}'")
        await callback.answer("❌ Ошибка формата времени")
        return
    
    try:
        # Проверяем, если это "завтра утром"
        if time_str == "07:00":
            # Создаем datetime для завтра в 7:00
            tomorrow = datetime.now() + timedelta(days=1)
            departure_datetime = tomorrow.replace(hour=7, minute=0, second=0, microsecond=0)
            await state.update_data(departure_time=departure_datetime)
            logger.info(f"Set departure time for tomorrow morning: {departure_datetime}")
        else:
            # Обычное время сегодня
            departure_time = datetime.strptime(time_str, "%H:%M").time()
            # Создаем datetime для сегодня
            today = datetime.now()
            departure_datetime = today.replace(hour=departure_time.hour, minute=departure_time.minute, second=0, microsecond=0)
            await state.update_data(departure_time=departure_datetime)
            logger.info(f"Successfully parsed time: {departure_datetime}")
        
        await callback.message.answer(
            "*Теперь введите описание поездки (необязательно):*", 
            parse_mode="Markdown",
            reply_markup=skip_description_keyboard()
        )
        await state.set_state(Trips.description)
        await callback.answer()
    except ValueError as e:
        logger.error(f"Error parsing time: '{time_str}', error: {e}")
        await callback.answer("❌ Ошибка формата времени")


@router.callback_query(F.data == "custom_time")
async def custom_time_selected(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора пользовательского времени"""
    # Проверяем, что callback отправлен в личном чате
    if callback.message.chat.type != "private":
        await callback.answer("❌ Эта функция доступна только в личных сообщениях с ботом")
        return
    
    await callback.message.answer("📅 *Введите время отправления (ЧЧ:ММ):*", parse_mode="Markdown")
    await state.set_state(Trips.departure_time)
    await callback.answer()


@router.message(StateFilter(Trips.origin))
async def trip_origin(message: types.Message, state: FSMContext):
    # Проверяем, что сообщение отправлено в личном чате
    if message.chat.type != "private":
        return
    
    logger.info(f"User {message.from_user.id} entered trip origin: {message.text}")
    await state.update_data(origin=message.text)
    await message.answer("🏁 *Введите конечную точку поездки:*", parse_mode="Markdown")
    await state.set_state(Trips.destination)


@router.message(StateFilter(Trips.destination))
async def trip_destination(message: types.Message, state: FSMContext):
    # Проверяем, что сообщение отправлено в личном чате
    if message.chat.type != "private":
        return
    
    logger.info(f"User {message.from_user.id} entered trip destination: {message.text}")
    await state.update_data(destination=message.text)
    await message.answer(
        "⏰ *Выберите время отправления:*",
        parse_mode="Markdown",
        reply_markup=quick_time_keyboard()
    )


@router.message(StateFilter(Trips.departure_time))
async def trip_departure_time(message: types.Message, state: FSMContext):
    # Проверяем, что сообщение отправлено в личном чате
    if message.chat.type != "private":
        return
    
    try:
        # Парсим введенное время
        departure_time = datetime.strptime(message.text, "%H:%M").time()
        
        # Создаем datetime для сегодня
        today = datetime.now()
        departure_datetime = today.replace(hour=departure_time.hour, minute=departure_time.minute, second=0, microsecond=0)
        
        logger.info(f"User {message.from_user.id} entered trip departure time: {departure_datetime}")
        await state.update_data(departure_time=departure_datetime)
        await message.answer(
            "*Теперь введите описание поездки (необязательно):*", 
            parse_mode="Markdown",
            reply_markup=skip_description_keyboard()
        )
        await state.set_state(Trips.description)
    except ValueError:
        logger.warning(f"User {message.from_user.id} entered invalid time format: {message.text}")
        await message.answer("❌ *Неверный формат времени. Попробуйте снова (в формате ЧЧ:ММ).*", parse_mode="Markdown")


@router.callback_query(F.data == "skip_description")
@db_session
async def skip_description(callback: types.CallbackQuery, state: FSMContext, session):
    """Обработчик для пропуска описания поездки"""
    # Проверяем, что callback отправлен в личном чате
    if callback.message.chat.type != "private":
        await callback.answer("❌ Эта функция доступна только в личных сообщениях с ботом")
        return
    
    data = await state.get_data()
    
    # Создаем поездку без описания
    trip = create_trip(
        session,
        user_id=callback.from_user.id,
        origin=data['origin'],
        destination=data['destination'],
        departure_time=data['departure_time'],
        seats_available=None,
        price_per_seat=None,
        description=""
    )
    
    logger.info(f"Trip created successfully for user {callback.from_user.id} without description")
    
    await callback.message.answer("✅ Поездка опубликована!", reply_markup=keyboards_main_menu())
    
    # Формируем текст для публикации
    text = (f"*Новая поездка!*\n\n"
            f"📍 *Маршрут:* {trip.origin} → {trip.destination}\n"
            f"⏰ *Время отправления:* {trip.departure_time.strftime('%d.%m.%Y %H:%M')}")
    
    # Отправляем информацию о поездке в группу
    await callback.bot.send_message(
        GROUP_ID,
        text,
        parse_mode="Markdown",
        reply_markup=keyboards_driver(trip.user_id, trip.id)
    )
    await callback.bot.send_message(
        GROUP_ID_ALL,
        text,
        parse_mode="Markdown",
        reply_markup=keyboards_driver(trip.user_id, trip.id)
    )
    
    await state.clear()
    await callback.answer()


@router.message(StateFilter(Trips.description))
@db_session
async def finalize_trip_creation(message: types.Message, state: FSMContext, session):
    # Проверяем, что сообщение отправлено в личном чате
    if message.chat.type != "private":
        return
    
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
        seats_available=None,  # Не указываем количество мест
        price_per_seat=None,   # Не указываем цену
        description=description  # если описание None, будет сохранено как None
    )
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    logger.info(f"Trip created successfully for user {message.from_user.id}")
    # keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='❌ Отменить поездку', callback_data=f"cancel_trip:{trip.id}")]])
    # await message.answer("Если хотите отменить поездку нажмите на кнопку", reply_markup=keyboard)
    await message.answer("Поездка опубликована!", reply_markup=keyboards_main_menu())
    print(f"Регистрация {trip.user_id, trip.id}")
    text=( f"*Новая поездка!*\n\n"
        f"📍 *Маршрут:* {trip.origin} → {trip.destination}\n"
        f"⏰ *Время отправления:* {trip.departure_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"{f'📝*Дополнительно:* {trip.description}' if trip.description else ''}")
    # Отправляем информацию о поездке в группу
    await message.bot.send_message(
        GROUP_ID,
        text,
        parse_mode="Markdown",
        reply_markup=keyboards_driver(trip.user_id, trip.id)  # Без учета мест
    )
    await message.bot.send_message(
        GROUP_ID_ALL,
        text,
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
    # Проверяем, что callback отправлен в личном чате
    if callback.message.chat.type != "private":
        await callback.answer("❌ Эта функция доступна только в личных сообщениях с ботом")
        return
    
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
        f"{f'📝*Дополнительно:* {trip.description}' if trip.description else ''}"
    )

    # Формируем кнопку "Хочу забронировать"
    keyboard = keyboards_driver(callback.from_user.id, trip.id)

    # Отправляем сообщение с кнопкой
    await callback.message.answer(trip_message, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data == "search_trips")
@db_session
async def search_trips(callback: types.CallbackQuery, session):
    # Проверяем, что callback отправлен в личном чате
    if callback.message.chat.type != "private":
        await callback.answer("❌ Эта функция доступна только в личных сообщениях с ботом")
        return
    
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
    # Проверяем, что callback отправлен в личном чате
    if callback.message.chat.type != "private":
        await callback.answer("❌ Эта функция доступна только в личных сообщениях с ботом")
        return
    
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
        await callback.bot.delete_message(chat_id=GROUP_ID_ALL, message_id=trip.group_message_id)
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


async def send_promo_every_4_days(bot: Bot):
    """
    Отправляет промо-сообщение в группу каждые 4 дня в 10:00
    """
    while True:
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        
        # Вычисляем время следующего поста (каждые 4 дня в 10:00)
        # Если сейчас меньше 10:00, то пост будет сегодня в 10:00
        # Если больше 10:00, то пост будет через 4 дня в 10:00
        if now.hour < 10:
            next_post_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        else:
            next_post_time = now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=4)
        
        wait_seconds = (next_post_time - now).total_seconds()
        
        await asyncio.sleep(wait_seconds)
        
        # Отправляем промо-сообщение
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Открыть бота", url="https://t.me/num_po_puti_bot")]
            ]
        )
        
        # promo_message = (
        #     "🚗 Хочешь больше попутчиков? Переходи в новую группу!\n"
        #     "👋 Ты уже пользуешься нашей группой «Нам по пути» для поездок c Суворовского района и обратно? Отлично!\n\n"
        #     "🔹 Встречайте новую группу — «Нам по пути | Все районы»!\n"
        #     "✅ Больше маршрутов — не только Суворовский, но и любые направления\n"
        #     "✅ Еще больше водителей и пассажиров — больше шансов найти попутчика\n"
        #     "✅ Гибкость — поездки между любыми районами без ограничений\n"
        #     "✅ Телеграм бот - для удобства поиска и публикации маршрутов\n"
        #     "👉 Переходи и подписывайся: @num_po_puti\n\n"
        #     "Не ограничивай себя одним районом — путешествуй по всему городу дешево и удобно!"
        # )
        
        promo_message = (
            "🚗 *Нам по пути - Бот для попутчиков!*\n\n"
            "👋 *Находи попутчиков за 2 клика!*\n\n"
            "✨ *Что умеет бот:*\n"
            "• Быстрая регистрация \n"
            "• Быстрое время: через 30 мин, 1 час, 2 часа\n"
            "• Можно пропустить описание\n\n"
            "💡 *Экономь время и деньги на поездках!*\n\n"
            "🚀 *Попробуй прямо сейчас:*"
        )

        try:
            # Отправляем в основную группу
            await bot.send_message(
                chat_id="@suvorovskynam",
                text=promo_message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            # Отправляем в дополнительную группу, если она настроена
            if GROUP_ID_ALL:
                try:
                    await bot.send_message(
                        chat_id=GROUP_ID_ALL,
                        text=promo_message,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logger.error(f"Error sending promo message to GROUP_ID_ALL: {e}")
            
            logger.info("Promo message sent successfully (every 4 days)")
        except Exception as e:
            logger.error(f"Error sending promo message: {e}")

# Добавляем функцию для запуска планировщика
async def start_scheduler(bot: Bot):
    """
    Запускает планировщик отправки промо-сообщений каждые 4 дня
    """
    asyncio.create_task(send_promo_every_4_days(bot))


@router.message(Command(commands=["promo"]))
async def send_manual_promo(message: types.Message):
    """
    Команда для ручной отправки промо-сообщения (для администраторов)
    """
    # Проверяем, что команда отправлена в личном чате
    if message.chat.type != "private":
        return
    
    # Проверяем, что команда отправлена администратором (можно настроить список ID)
    admin_ids = [123456789]  # Замените на реальные ID администраторов
    
    if message.from_user.id not in admin_ids:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    promo_message = (
        "🚗 *Нам по пути - Бот для попутчиков!*\n\n"
        "👋 *Находи попутчиков за 2 клика!*\n\n"
        "✨ *Что умеет бот:*\n"
        "• Быстрая регистрация (только имя)\n"
        "• Готовые маршруты: Суворовский ↔ Центр, Аэропорт, Вокзал\n"
        "• Быстрое время: через 30 мин, 1 час, 2 часа\n"
        "• Можно пропустить описание\n\n"
        "💡 *Экономь время и деньги на поездках!*\n\n"
        "🚀 *Попробуй прямо сейчас:*"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Открыть бота", url="https://t.me/num_po_puti_bot")]
        ]
    )
    
    try:
        await message.answer(
            text=promo_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await message.answer("✅ Промо-сообщение отправлено!")
    except Exception as e:
        logger.error(f"Error sending manual promo message: {e}")
        await message.answer("❌ Ошибка при отправке промо-сообщения.")
