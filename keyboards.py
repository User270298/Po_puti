from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def keyboards_main_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Опубликовать поездку🚘", callback_data="publish_trip")],
                         [InlineKeyboardButton(text="Посмотреть все активные поездки📋", callback_data="search_trips")],

                         ])
    return keyboard

#
def keyboards_driver(user_id, trip_id):
    button_text = "Хочу поехать"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data=f"book_trip:{user_id}:{trip_id}")]
        ]
    )
    return keyboard


def description_choice_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="description_yes")],
            [InlineKeyboardButton(text="Нет", callback_data="description_no")]
        ]
    )
    return keyboard


def skip_description_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить описание", callback_data="skip_description")]
        ]
    )
    return keyboard


def quick_routes_keyboard():
    """Клавиатура с быстрыми шаблонами популярных маршрутов"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Суворовский → Центр", callback_data="quick_route:suvorovskiy:center")],
            [InlineKeyboardButton(text="🏢 Центр → Суворовский", callback_data="quick_route:center:suvorovskiy")],
            [InlineKeyboardButton(text="🚂 Ростов Главный → Центр", callback_data="quick_route:station:center")],
            [InlineKeyboardButton(text="📝 Свой маршрут", callback_data="custom_route")]
        ]
    )
    return keyboard


def quick_time_keyboard():
    """Клавиатура с быстрыми вариантами времени"""
    from datetime import datetime, timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # Округляем до ближайших 15 минут
    rounded_minute = (current_minute // 15) * 15
    if rounded_minute == 0:
        rounded_minute = 60
        current_hour += 1
    
    # Формируем варианты времени
    time_options = []
    
    # Через 30 минут
    time_30min = now + timedelta(minutes=30)
    time_30min_str = time_30min.strftime('%H:%M')
    time_options.append(f"⏰ Через 30 мин ({time_30min_str})")
    
    # Через час
    time_1hour = now + timedelta(hours=1)
    time_1hour_str = time_1hour.strftime('%H:%M')
    time_options.append(f"⏰ Через 1 час ({time_1hour_str})")
    
    # Через 2 часа
    time_2hour = now + timedelta(hours=2)
    time_2hour_str = time_2hour.strftime('%H:%M')
    time_options.append(f"⏰ Через 2 часа ({time_2hour_str})")
    
    # Завтра утром в 7:00
    tomorrow_morning = (now + timedelta(days=1)).replace(hour=7, minute=0)
    tomorrow_morning_str = tomorrow_morning.strftime('%H:%M')
    time_options.append(f"🌅 Завтра утром в 7:00")
    
    # Логируем callback_data для отладки
    logger.info(f"Generated callback_data: quick_time:{time_30min_str}, quick_time:{time_1hour_str}, quick_time:{time_2hour_str}, quick_time:{tomorrow_morning_str}")
    
    # Проверяем, что все строки времени корректны
    logger.info(f"Time strings: {time_30min_str}, {time_1hour_str}, {time_2hour_str}, {tomorrow_morning_str}")
    logger.info(f"Time strings types: {type(time_30min_str)}, {type(time_1hour_str)}, {type(time_2hour_str)}, {type(tomorrow_morning_str)}")
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=time_options[0], callback_data=f"quick_time:{time_30min_str}")],
            [InlineKeyboardButton(text=time_options[1], callback_data=f"quick_time:{time_1hour_str}")],
            [InlineKeyboardButton(text=time_options[2], callback_data=f"quick_time:{time_2hour_str}")],
            [InlineKeyboardButton(text=time_options[3], callback_data=f"quick_time:{tomorrow_morning_str}")],
            [InlineKeyboardButton(text="📝 Свое время", callback_data="custom_time")]
        ]
    )
    return keyboard
