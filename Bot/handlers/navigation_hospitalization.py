import httpx
from telegram import Update
from telegram.ext import ContextTypes
from .auth import require_token
from ..utils import *
from ..constants import *


async def handle_current_hospitalization(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    patient_id = context.user_data.get("user_id")
    token = context.user_data.get("token")

    if not token:
        await require_token(update, context)
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_CURRENT_HOSPITALIZATION,
                json={"patient_id": patient_id},
                headers={"Authorization": f"Bearer {token}"}
            )

        data = await handle_api_response(response, context, update, lang)
        if data is False:
            return

        if data.get("active"):
            context.user_data["current_hospital_visit_id"] = data["visit_id"]
            context.user_data["menu_state"] = "current_hosp"
            await update.message.reply_text(
                TEXTS["current_hospital_prompt"][lang],
                reply_markup=keyboard_from_data([
                    [TEXTS["prescriptions_btn"][lang]],
                    [TEXTS["vitals_btn"][lang]],
                    [TEXTS["back_btn"][lang]]
                ])
            )
        else:
            await update.message.reply_text(TEXTS["no_current_hospital"][lang])

    except Exception as e:
        print("Ошибка:", e)
        await update.message.reply_text(TEXTS["api_response_error"][lang])


async def handle_prescriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    context.user_data["menu_state"] = "select_presc_day"
    await update.message.reply_text(
        TEXTS["select_presc_day_prompt"][lang],
        reply_markup=keyboard_from_data([TEXTS["prescriptions_day_buttons"][lang], [TEXTS["back_btn"][lang]]])
    )


async def handle_prescriptions_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    text = update.message.text

    visit_id = context.user_data.get("current_hospital_visit_id")
    patient_id = context.user_data.get("user_id")
    token = context.user_data.get("token")

    day_buttons = TEXTS["prescriptions_day_buttons"][lang]
    date_value = "today" if text == day_buttons[0] else "yesterday"

    if not token or not visit_id:
        await require_token(update, context)
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_PRESCRIPTIONS,
                json={"visit_id": visit_id, "patient_id": patient_id, "date": date_value},
                headers={"Authorization": f"Bearer {token}"}
            )

        data = await handle_api_response(response, context, update, lang)
        if data is False:
            return

        if not data:
            await update.message.reply_text(TEXTS["no_prescriptions"][lang])
            return

        lines = []
        for p in data:
            title = f"*{p['ass_remarks']}*"
            time = f"{TEXTS['presc_time_prefix'][lang]} {p['ass_time']}"
            status = TEXTS["presc_delivered"][lang] if p["ass_delivered"] else TEXTS["presc_not_delivered"][lang]
            lines.append(f"{title}\n{time}\n{status}\n")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown"
        )

    except Exception as e:
        print("Ошибка при получении назначений:", e)
        await update.message.reply_text(TEXTS["api_response_error"][lang])


async def handle_vitals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    context.user_data["menu_state"] = "select_vitals_day"
    await update.message.reply_text(
        TEXTS["select_presc_day_prompt"][lang],
        reply_markup=keyboard_from_data([TEXTS["prescriptions_day_buttons"][lang], [TEXTS["back_btn"][lang]]])
    )


async def handle_vitals_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    text = update.message.text

    visit_id = context.user_data.get("current_hospital_visit_id")
    patient_id = context.user_data.get("user_info", {}).get("id")
    token = context.user_data.get("token")

    day_buttons = TEXTS["prescriptions_day_buttons"][lang]
    date_value = "today" if text == day_buttons[0] else "yesterday"

    if not token or not visit_id:
        await require_token(update, context)
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_VITALS,
                json={"visit_id": visit_id, "date": date_value, "patient_id": patient_id},
                headers={"Authorization": f"Bearer {token}"}
            )

        data = await handle_api_response(response, context, update, lang)
        if data is False:
            return

        if not any(data.values()):
            await update.message.reply_text(TEXTS["no_vitals"][lang])
            return

        lines = []

        if data["temperature"]:
            lines.append(f"*{TEXTS['vital_temp'][lang]}*")
            for t in data["temperature"]:
                lines.append(f"{t['log_time']}: {t['log_value']}°C")
            lines.append("")

        if data["saturation"]:
            lines.append(f"*{TEXTS['vital_saturation'][lang]}*")
            for s in data["saturation"]:
                lines.append(f"{s['log_time']}: {s['log_value']}%")
            lines.append("")

        if data["pressure"]:
            lines.append(f"*{TEXTS['vital_pressure'][lang]}*")
            for p in data["pressure"]:
                bp = f"{p['log_up']}/{p['log_low']}"
                pulse = f"{TEXTS['vital_pulse'][lang]}: {p['log_pulse']}"
                lines.append(f"{p['log_time']}: {bp}, {pulse}")
            lines.append("")

        await update.message.reply_text(
            "\n".join(lines).strip(),
            parse_mode="Markdown"
        )

    except Exception as e:
        print("Ошибка при получении показателей:", e)
        await update.message.reply_text(TEXTS["api_response_error"][lang])
