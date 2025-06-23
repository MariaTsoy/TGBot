from telegram import ReplyKeyboardMarkup


LANG_KEYBOARD = ReplyKeyboardMarkup(
    [["Русский 🇷🇺", "Қазақша 🇰🇿", "English 🇬🇧"]],
    resize_keyboard=True, one_time_keyboard=True
)


LANG_CODES = {
    "Русский 🇷🇺": "ru",
    "Қазақша 🇰🇿": "kz",
    "English 🇬🇧": "en"
}
