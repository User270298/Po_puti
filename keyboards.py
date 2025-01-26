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
