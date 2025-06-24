import nest_asyncio
import asyncio
from Bot.handlers.start import *
from startup import *
from Bot.handlers.navigation_menu import *
from Bot.handlers.navigation_personal_data import *
from Bot.handlers.navigation_hospitalization import *
from Bot.handlers.navigation_schedule import *
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

setup()
nest_asyncio.apply()

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    text = update.message.text
    is_authenticated = "user_info" in context.user_data

    print("➡️ menu_handler triggered, text =", text)
    print("auth_step =", context.user_data.get("auth_step"))

    if context.user_data.get("auth_step") == "awaiting_iin":
        if text == TEXTS["main_menu_btn"][lang]:
            context.user_data.pop("auth_step", None)
            context.user_data.pop("phone_for_auth", None)
            await handle_menu(update, context)
            return

        iin = update.message.text.strip()
        phone = context.user_data.get("phone_for_auth")
        telegram_id = update.effective_user.id

        response = await check_user_by_phone_and_iin(phone, iin, telegram_id)

        if not response:
            await update.message.reply_text(TEXTS["api_error"][lang])
        elif response.get("found"):
            data = response["data"]
            token = response.get("token")

            context.user_data["user_info"] = data
            context.user_data["token"] = token
            context.user_data["user_id"] = data.get("id")
            context.user_data["was_authenticated_once"] = True
            context.user_data.pop("auth_step", None)
            context.user_data.pop("phone_for_auth", None)

            full_name = f'{data["ptn_lname"]} {data["ptn_gname"]} {data["ptn_mname"]}'.strip()
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
            if error == "wrong_iin":
                await update.message.reply_text(TEXTS["wrong_iin"][lang])
            elif error == "not_found":
                await update.message.reply_text(TEXTS["not_found"][lang].format(phone=phone))
            else:
                await update.message.reply_text(TEXTS["not_found"][lang].format(phone=phone))

            context.user_data.clear()

            contact_btn = KeyboardButton(TEXTS["auth_button"][lang], request_contact=True)
            menu_btn = KeyboardButton(TEXTS["main_menu_btn"][lang])
            keyboard = ReplyKeyboardMarkup([[contact_btn], [menu_btn]], resize_keyboard=True)

            await update.message.reply_text(TEXTS["auth_prompt"][lang], reply_markup=keyboard)

        return

    if not text:
        return

    if text in ["Личный кабинет 💼", "Жеке кабинет 💼", "Account 💼"]:
        await handle_personal_account(update, context)

    elif text == TEXTS["back_btn"][lang]:
        await handle_back(update, context)

    elif text == TEXTS["main_menu_btn"][lang]:
        context.user_data.pop("auth_step", None)
        context.user_data.pop("phone_for_auth", None)
        await handle_menu(update, context)

    elif text == TEXTS["menu_main"][lang][0][0]:
        await handle_contacts(update, context)

    elif text == TEXTS["menu_main"][lang][1][0]:
        await start(update, context)

    elif text == TEXTS["menu_after_login"][lang][0][0]:
        await handle_personal_data(update, context)

    elif text == TEXTS["menu_after_login"][lang][0][1]:  # "Записи"
        await handle_schedule(update, context)

    elif text == TEXTS["personal_menu"][lang][0][0]:
        await handle_visits(update, context)

    elif text == TEXTS["personal_menu"][lang][0][1]:
        await handle_discharges(update, context)

    elif context.user_data.get("menu_state") == "after_discharge" and text not in TEXTS["back_btn"][lang]:
        await handle_discharge_types(update, context)

    elif context.user_data.get("menu_state") == "after_discharge_dates" and text not in TEXTS["back_btn"][lang]:
        await handle_discharge_dates(update, context)

    elif text == TEXTS["personal_menu"][lang][1][0]:
        await handle_current_hospitalization(update, context)

    elif text == TEXTS["prescriptions_btn"][lang]:
        await handle_prescriptions(update, context)

    elif context.user_data.get("menu_state") == "select_presc_day" and text in TEXTS["prescriptions_day_buttons"][lang]:
        await handle_prescriptions_day(update, context)

    elif text == TEXTS["vitals_btn"][lang]:
        await handle_vitals(update, context)

    elif context.user_data.get("menu_state") == "select_vitals_day" and text in TEXTS["prescriptions_day_buttons"][lang]:
        await handle_vitals_day(update, context)

async def main():
    TOKEN = "7639326206:AAFXGF1O5_uT333lexZ9IUclyrCiRlFurig"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(Русский|Қазақша|English).*$"), set_language))
    app.add_handler(MessageHandler(filters.Regex(".*"), menu_handler))
    app.add_handler(MessageHandler(
        filters.CONTACT | filters.Regex(r"[\d\+\-\(\)\s]{10,}"),
        handle_phone
    ))

    print("Bot's running.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
