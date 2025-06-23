from telegram import Update
from telegram.ext import ContextTypes
from ..constants import LANG_KEYBOARD, LANG_CODES
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
