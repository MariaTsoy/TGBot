import httpx
import re
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from ..texts import TEXTS
from ..keyboard import keyboard_from_data


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text

    phone = re.sub(r"[^\d+]", "", phone)
    if phone.startswith("8"):
        phone = "+7" + phone[1:]
    elif phone.startswith("7"):
        phone = "+7" + phone[1:]

    context.user_data["phone_for_auth"] = phone
    context.user_data["auth_step"] = "awaiting_iin"

    await update.message.reply_text(TEXTS["enter_iin_prompt"][lang])


async def check_user_by_phone_and_iin(phone, iin, telegram_id):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url="http://localhost:5000/check_user",
                json={
                    "phone": phone,
                    "iin": iin,
                    "telegram_id": telegram_id
                }
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print("Ошибка API:", e)
    return {"found": False}


async def require_token(update, context):
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(TEXTS["session_expired"][lang])
    contact_button = KeyboardButton(TEXTS["auth_button"][lang], request_contact=True)
    keyboard = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(TEXTS["auth_prompt"][lang], reply_markup=keyboard)



