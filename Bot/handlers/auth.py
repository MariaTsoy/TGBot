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

    response = await check_user_by_phone(phone)

    if response["found"]:
        data = response["data"]
        token = response.get("token")

        context.user_data["user_info"] = data
        context.user_data["token"] = token
        context.user_data["user_id"] = data.get("id")
        context.user_data["was_authenticated_once"] = True

        full_name = f'{data["ptn_lname"]} {data["ptn_gname"]} {data["ptn_mname"]}'.strip()
        context.user_data["full_name"] = full_name
        context.user_data["main_menu_prompt"] = TEXTS["main_menu_prompt"][lang]

        await update.message.reply_text(
            TEXTS["auth_success_first"][lang].format(
                phone=phone,
                full_name=full_name,
                main_menu=TEXTS["main_menu_prompt"][lang]
            ),
            reply_markup=keyboard_from_data(TEXTS["menu_after_login"][lang])
        )
    else:
        await update.message.reply_text(TEXTS["not_found"][lang].format(phone=phone))


async def check_user_by_phone(phone_number):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url="http://localhost:5000/check_user",
                json={"phone": phone_number}
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API status: {response.status_code}")
                return {"found": False}
        except httpx.RequestError as e:
            print(f"API request error: {e}")
            return {"found": False}


async def require_token(update, context):
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(TEXTS["session_expired"][lang])
    contact_button = KeyboardButton(TEXTS["auth_button"][lang], request_contact=True)
    keyboard = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(TEXTS["auth_prompt"][lang], reply_markup=keyboard)



