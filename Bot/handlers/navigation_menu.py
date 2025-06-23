from telegram import Update
from telegram.ext import ContextTypes
from ..keyboard import *


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    await update.message.reply_text(
        TEXTS["main_menu_prompt"][lang],
        reply_markup=keyboard_from_data(TEXTS["menu_main"][lang])
    )


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    state = context.user_data.get("menu_state")

    if state == "after_discharge":
        context.user_data["menu_state"] = "personal_menu"
        await update.message.reply_text(
            TEXTS["personal_data_prompt"][lang],
            reply_markup=keyboard_from_data(TEXTS["personal_menu"][lang])
        )
    elif state == "after_discharge_dates":
        context.user_data["menu_state"] = "after_discharge"
        await update.message.reply_text(
            TEXTS["personal_data_prompt"][lang],
            reply_markup=keyboard_from_data(context.user_data["discharge_types_menu"])
        )
    elif state == "current_hosp":
        context.user_data["menu_state"] = "personal_menu"
        await update.message.reply_text(
            TEXTS["personal_data_prompt"][lang],
            reply_markup=keyboard_from_data(TEXTS["personal_menu"][lang])
        )
    elif state == "select_presc_day":
        context.user_data["menu_state"] = "current_hosp"
        await update.message.reply_text(
            TEXTS["current_hospital_prompt"][lang],
            reply_markup=keyboard_from_data([[TEXTS["prescriptions_btn"][lang], TEXTS["vitals_btn"][lang]], [TEXTS["back_btn"][lang]]])
        )
    elif state == "select_vitals_day":
        context.user_data["menu_state"] = "current_hosp"
        await update.message.reply_text(
            TEXTS["current_hospital_prompt"][lang],
            reply_markup=keyboard_from_data([[TEXTS["prescriptions_btn"][lang], TEXTS["vitals_btn"][lang]], [TEXTS["back_btn"][lang]]])
        )
    else:
        context.user_data["menu_state"] = "main_menu_prompt"
        await update.message.reply_text(
            TEXTS["auth_success_repeat"][lang].format(
                full_name=context.user_data.get("full_name", ""),
                main_menu=context.user_data.get("main_menu_prompt", "")),
            reply_markup=keyboard_from_data(TEXTS["menu_after_login"][lang])
        )


async def handle_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    await update.message.reply_text(
        TEXTS["contacts_info"][lang],
        parse_mode="Markdown",
        reply_markup=keyboard_single_from_menu("menu_after_login", lang)
    )


