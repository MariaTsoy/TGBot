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


API_BASE_URL = "http://localhost:5000"

API_CHECK_USER = f"{API_BASE_URL}/check_user"
API_CHECK_TELEGRAM = f"{API_BASE_URL}/check_telegram"
API_CURRENT_HOSPITALIZATION = f"{API_BASE_URL}/current_hospitalization"
API_PRESCRIPTIONS = f"{API_BASE_URL}/prescriptions"
API_VITALS = f"{API_BASE_URL}/vitals"
API_VISITS_COUNT = f"{API_BASE_URL}/visits_count"
API_DOWNLOAD_PDF = f"{API_BASE_URL}/download_pdf"
API_RESEARCHES = f"{API_BASE_URL}/researches"
API_SCHEDULE = f"{API_BASE_URL}/schedule"


BOT_TOKEN = "7639326206:AAFXGF1O5_uT333lexZ9IUclyrCiRlFurig"
