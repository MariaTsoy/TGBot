import httpx
import re
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from .navigation_menu import handle_menu
from ..keyboard import keyboard_from_data
from ..texts import TEXTS
from ..constants import *


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                url=API_CHECK_USER,
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
            print("Ошибка запроса check_user:", e)

    return {"found": False, "error": "api_response_error"}


async def verify_token(context: ContextTypes.DEFAULT_TYPE) -> bool:
    telegram_id = context._user_id
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_CHECK_TELEGRAM,
                                         json={"telegram_id": telegram_id})
            if response.status_code == 200:
                data = response.json()
                if data.get("found"):
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


async def process_iin_step(update, context, lang, text):
    if text == TEXTS["main_menu_btn"][lang]:
        context.user_data.pop("auth_step", None)
        context.user_data.pop("phone_for_auth", None)
        await handle_menu(update, context)
        return

    iin = text.strip()
    phone = context.user_data.get("phone_for_auth")
    telegram_id = update.effective_user.id

    response = await check_user_by_phone_and_iin(phone, iin, telegram_id)

    if not response:
        await update.message.reply_text(TEXTS["api_response_error"][lang])
        return

    if response.get("found"):
        data = response["data"]
        token = response.get("token")
        full_name = f'{data["ptn_lname"]} {data["ptn_gname"]} {data["ptn_mname"]}'.strip()

        context.user_data.update({
            "user_info": data,
            "token": token,
            "user_id": data.get("id"),
            "was_authenticated_once": True,
            "full_name": full_name,
            "main_menu_prompt": TEXTS["main_menu_prompt"][lang]
        })
        context.user_data.pop("auth_step", None)
        context.user_data.pop("phone_for_auth", None)

        await update.message.reply_text(
            TEXTS["auth_success_first"][lang].format(
                phone=phone,
                full_name=full_name,
                main_menu=TEXTS["main_menu_prompt"][lang]
            ),
            reply_markup=keyboard_from_data(TEXTS["menu_after_login"][lang])
        )
    else:
        error = response.get("error")
        msg = TEXTS["not_found"][lang].format(phone=phone)
        if error == "wrong_iin":
            msg = TEXTS["wrong_iin"][lang]
        await update.message.reply_text(msg)

        context.user_data.clear()
        contact_btn = KeyboardButton(TEXTS["auth_button"][lang], request_contact=True)
        menu_btn = KeyboardButton(TEXTS["main_menu_btn"][lang])
        keyboard = ReplyKeyboardMarkup([[contact_btn], [menu_btn]], resize_keyboard=True)
        await update.message.reply_text(TEXTS["auth_prompt"][lang], reply_markup=keyboard)
