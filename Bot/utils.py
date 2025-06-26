from keyboard import *


async def handle_api_response(response, context, update, lang):
    if response.status_code == 401:
        context.user_data.pop("token", None)
        context.user_data.pop("user_id", None)
        context.user_data.pop("user_info", None)
        await update.message.reply_text(
            TEXTS["session_expired"][lang],
            reply_markup=build_main_menu(lang)
        )
        return False

    if response.status_code != 200:
        await update.message.reply_text(TEXTS["api_response_error"][lang])
        return False

    data = response.json()
    if "error" in data:
        await update.message.reply_text(TEXTS["api_response_error"][lang])
        return False

    return data
