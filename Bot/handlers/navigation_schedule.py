from telegram import Update
from telegram.ext import ContextTypes
from ..keyboard import *
import httpx
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


async def handle_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    token = context.user_data.get("token")
    patient_id = context.user_data.get("user_info", {}).get("id")

    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.post(
                "http://localhost:5000/schedule",
                json={"patient_id": patient_id, "lang": lang},
                headers=headers
            )

        data = response.json()

        if response.status_code == 401 or "error" in data:
            await update.message.reply_text(
                TEXTS["session_expired"][lang],
                reply_markup=build_main_menu(lang)
            )
            return

        records = data.get("records", [])
        if not records:
            await update.message.reply_text(
                TEXTS["no_schedule"][lang],
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(TEXTS["make_appointment_btn"][lang], url="https://hemcenter.kz/onlineorder/")]
                ])
            )
            return

        lines = [f"*{TEXTS['your_schedule'][lang]}:*"]
        for rec in records:
            lines.append(
                f"{rec['department']}\n"
                f"{rec['schp_date']} {rec['schp_time']}\n"
                f"{rec['event_type']}\n"
                f"{TEXTS['doctor'][lang]}: {rec['doctor_name']}"
            )

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(TEXTS["make_appointment_btn"][lang], url="https://hemcenter.kz/onlineorder/")]
            ])
        )

    except Exception as e:
        print("Ошибка при получении записей:", e)
        await update.message.reply_text(
            TEXTS["api_response_error"][lang],
            reply_markup=build_main_menu(lang)
        )
