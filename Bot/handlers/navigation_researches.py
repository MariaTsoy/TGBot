import httpx
from telegram import Update
from telegram.ext import ContextTypes
from Bot.texts import TEXTS
from ..constants import *


async def handle_researches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    token = context.user_data.get("token")
    patient_id = context.user_data.get("user_id")

    if not token or not patient_id:
        await update.message.reply_text(TEXTS["session_expired"][lang])
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                API_RESEARCHES,
                json={"patient_id": patient_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
        except Exception as e:
            print("Ошибка при запросе /researches:", e)
            await update.message.reply_text(TEXTS["api_response_error"][lang])
            return

    if response.status_code == 401:
        await update.message.reply_text(TEXTS["session_expired"][lang])
        return
    elif response.status_code != 200:
        await update.message.reply_text(TEXTS["api_response_error"][lang])
        return

    data = response.json()
    if data.get("error") == "no_hospitalization":
        await update.message.reply_text(TEXTS["no_hospitalizations"][lang])
        return

    researches = data.get("researches")
    if researches is None:
        await update.message.reply_text(TEXTS["api_response_error"][lang])
        return

    if not researches:
        await update.message.reply_text(TEXTS["no_researches"][lang])
        return

    message = f"<b>{TEXTS['last_researches'][lang]}</b>\n\n"
    for day_data in data["researches"]:
        date = day_data["date_sample"]
        message += f"<b>{TEXTS['sample_date'][lang]} {date}</b>\n"
        for item in day_data["items"]:
            message += f"{item['rsch_name']}\n"
            if item["date_result"]:
                message += f"{TEXTS['result_date'][lang]} {item['date_result']}\n"
            else:
                message += f"{TEXTS['result_date'][lang]} {TEXTS['result_not_ready'][lang]}\n"

            result = item["result_text"] or TEXTS["result_empty"][lang]
            message += f"{TEXTS['result'][lang]} {result}\n\n"

    await update.message.reply_text(message, parse_mode="HTML")
