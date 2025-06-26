import nest_asyncio
import asyncio
from startup import *
from constants import *
from Bot.handlers.navigation_menu import *
from Bot.handlers.navigation_personal_data import *
from Bot.handlers.navigation_hospitalization import *
from Bot.handlers.navigation_schedule import *
from Bot.handlers.navigation_researches import *
from Bot.handlers.auth import *
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters)


setup()
nest_asyncio.apply()


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    text = update.message.text
    is_authenticated = "user_info" in context.user_data

    if context.user_data.get("auth_step") == "awaiting_iin":
        await process_iin_step(update, context, lang, text)
        return

    if not text:
        return

    if text == TEXTS["menu_main"][lang][0][1]:
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

    elif text == TEXTS["menu_after_login"][lang][0][1]:
        await handle_schedule(update, context)

    elif text == TEXTS["menu_after_login"][lang][1][0]:
        await handle_researches(update, context)

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
    TOKEN = BOT_TOKEN
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
