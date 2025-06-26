import httpx
from telegram import Update
from telegram.ext import ContextTypes
from ..constants import *
from ..texts import TEXTS
from ..keyboard import keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_lang_msg = (
        f"{TEXTS['choose_lang']['ru']}\n"
        f"{TEXTS['choose_lang']['kz']}\n"
        f"{TEXTS['choose_lang']['en']}"
    )
    await update.message.reply_text(full_lang_msg, reply_markup=LANG_KEYBOARD)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    lang = LANG_CODES.get(choice)
    if lang:
        context.user_data["lang"] = lang
        await update.message.reply_text(
            TEXTS["main_menu_prompt"][lang],
            reply_markup=keyboard("menu_main", lang)
        )

async def try_auto_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_CHECK_TELEGRAM, json={"telegram_id": telegram_id})
            if response.status_code == 200:
                data = response.json()
                if data["found"]:
                    context.user_data["user_info"] = data["data"]
                    context.user_data["token"] = data["token"]
                    context.user_data["user_id"] = data["data"]["id"]
                    context.user_data["was_authenticated_once"] = True
                    return True
    except Exception as e:
        print("Auto-login error:", e)

    return False
