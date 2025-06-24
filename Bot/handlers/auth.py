import httpx
import re
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from ..texts import TEXTS


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📞 handle_phone triggered")

    lang = context.user_data.get("lang", "ru")

    if context.user_data.get("auth_step") == "awaiting_iin":
        return

    if update.message.contact and update.message.contact.user_id != update.effective_user.id:
        await update.message.reply_text(TEXTS["wrong_contact"][lang])
        return

    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    phone = re.sub(r"[^\d+]", "", phone)
    if phone.startswith("8"):
        phone = "+7" + phone[1:]
    elif phone.startswith("7"):
        phone = "+7" + phone[1:]

    context.user_data["phone_for_auth"] = phone
    context.user_data["auth_step"] = "awaiting_iin"

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(TEXTS["main_menu_btn"][lang])]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await update.message.reply_text(
        TEXTS["enter_iin_prompt"][lang],
        reply_markup=keyboard
    )


async def check_user_by_phone_and_iin(phone, iin, telegram_id):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url="http://localhost:5000/check_user",
                json={
                    "phone": phone,
                    "iin": iin,
                    "telegram_id": telegram_id
                },
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                if not data.get("found"):
                    return {"found": False, "error": data.get("error", "not_found")}
                return data
            else:
                print("⚠️ Ошибка ответа сервера:", response.status_code)
        except Exception as e:
            print("❌ Ошибка запроса check_user:", e)

    return {"found": False, "error": "api_error"}


async def verify_token(context: ContextTypes.DEFAULT_TYPE) -> bool:
    telegram_id = context._user_id
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:5000/check_telegram", json={"telegram_id": telegram_id})
            if response.status_code == 200:
                data = response.json()
                if data.get("found"):
                    # 💡 если токен и данные есть — сразу заполняем context.user_data
                    context.user_data["user_info"] = data["data"]
                    context.user_data["token"] = data["token"]
                    context.user_data["user_id"] = data["data"]["id"]
                    context.user_data["was_authenticated_once"] = True
                    return True
    except Exception as e:
        print("Token verification error:", e)
    return False


async def require_token(update, context):
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(TEXTS["session_expired"][lang])

    contact_button = KeyboardButton(TEXTS["auth_button"][lang], request_contact=True)
    menu_button = KeyboardButton(TEXTS["main_menu_btn"][lang])
    keyboard = ReplyKeyboardMarkup([[contact_button], [menu_button]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(TEXTS["auth_prompt"][lang], reply_markup=keyboard)
