from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

location_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отправить геолокацию", request_location=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

timezone_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Калининград (МСК-1)", callback_data="tz:Europe/Kaliningrad"
            )
        ],
        [InlineKeyboardButton(text="Москва (МСК)", callback_data="tz:Europe/Moscow")],
        [InlineKeyboardButton(text="Самара (МСК+1)", callback_data="tz:Europe/Samara")],
        [
            InlineKeyboardButton(
                text="Екатеринбург (МСК+2)", callback_data="tz:Asia/Yekaterinburg"
            )
        ],
        [InlineKeyboardButton(text="Омск (МСК+3)", callback_data="tz:Asia/Omsk")],
        [
            InlineKeyboardButton(
                text="Красноярск (МСК+4)", callback_data="tz:Asia/Krasnoyarsk"
            )
        ],
        [InlineKeyboardButton(text="Иркутск (МСК+5)", callback_data="tz:Asia/Irkutsk")],
        [InlineKeyboardButton(text="Якутск (МСК+6)", callback_data="tz:Asia/Yakutsk")],
        [
            InlineKeyboardButton(
                text="Владивосток (МСК+7)", callback_data="tz:Asia/Vladivostok"
            )
        ],
        [InlineKeyboardButton(text="Магадан (МСК+8)", callback_data="tz:Asia/Magadan")],
        [
            InlineKeyboardButton(
                text="Камчатка (МСК+9)", callback_data="tz:Asia/Kamchatka"
            )
        ],
        [InlineKeyboardButton(text="Я не знаю", callback_data="tz:Dont/Know")],
    ]
)

dont_know_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Поделится локацией (авто-поиск)", callback_data="tz_choice:geo"
            )
        ],
        [
            InlineKeyboardButton(
                text="Оставить по умолчанию (МСК)", callback_data="tz_choice:default"
            )
        ],
    ]
)
