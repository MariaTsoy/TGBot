import io
from .auth import *
from .start import *
from ..utils import *
from ..constants import *
from telegram import ReplyKeyboardMarkup, KeyboardButton


async def handle_personal_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    await update.message.reply_text(
        TEXTS["personal_data_prompt"][lang],
        reply_markup=keyboard_from_data(TEXTS["personal_menu"][lang]),
    )


async def handle_personal_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    if "token" not in context.user_data:
        auto_login_success = await try_auto_login(update, context)
        if not auto_login_success:
            contact_btn = KeyboardButton(TEXTS["auth_button"][lang], request_contact=True)
            menu_btn = KeyboardButton(TEXTS["main_menu_btn"][lang])
            keyboard = ReplyKeyboardMarkup([[contact_btn], [menu_btn]],
                                           resize_keyboard=True, one_time_keyboard=True)

            await update.message.reply_text(TEXTS["auth_prompt"][lang], reply_markup=keyboard)
            return

    token_valid = await verify_token(context)
    if not token_valid:
        context.user_data.clear()

        contact_btn = KeyboardButton(TEXTS["auth_button"][lang], request_contact=True)
        menu_btn = KeyboardButton(TEXTS["main_menu_btn"][lang])
        keyboard = ReplyKeyboardMarkup([[contact_btn], [menu_btn]],
                                       resize_keyboard=True, one_time_keyboard=True)

        await update.message.reply_text(TEXTS["session_expired"][lang], reply_markup=keyboard)
        return

    user_info = context.user_data.get("user_info", {})
    full_name = (f'{user_info.get("ptn_lname", "")} '
                 f'{user_info.get("ptn_gname", "")} {user_info.get("ptn_mname", "")}').strip()
    phone = user_info.get("ptn_mobile", "📞")
    main_menu = TEXTS["main_menu_prompt"][lang]

    if context.user_data.get("was_authenticated_once"):
        reply_text = TEXTS["auth_success_repeat"][lang].format(full_name=full_name, main_menu=main_menu)
    else:
        reply_text = TEXTS["auth_success_first"][lang].format(phone=phone, full_name=full_name, main_menu=main_menu)
        context.user_data["was_authenticated_once"] = True

    await update.message.reply_text(
        reply_text,
        reply_markup=keyboard_from_data(TEXTS["menu_after_login"][lang])
    )


async def handle_visits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    patient_id = context.user_data.get("user_id")
    token = context.user_data.get("token")

    if not token:
        await require_token(update, context)
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_VISITS_COUNT,
                json={"patient_id": patient_id, "lang": lang},
                headers={"Authorization": f"Bearer {token}"}
            )

        data = await handle_api_response(response, context, update, lang)
        if data is False:
            return

        if not data:
            await update.message.reply_text(
                TEXTS["no_visits"][lang],
                reply_markup=keyboard_from_data(TEXTS["back_menu"][lang])
            )
            return

        lines = [TEXTS["visit_count_title"][lang]]
        for v in data.values():
            lines.append(f"- {v['name']}: {v['count']}")
            for d in v["dates"]:
                closing = d["closing"] or TEXTS["visit_still_open"][lang]
                lines.append(f"  {d['incoming']} – {closing}")

        await update.message.reply_text(
            "\n".join(lines),
            reply_markup=keyboard_from_data(TEXTS["personal_menu"][lang])
        )

    except Exception as e:
        print("Ошибка:", e)
        await update.message.reply_text(TEXTS["api_response_error"][lang])


async def handle_discharges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    patient_id = context.user_data.get("user_id")
    token = context.user_data.get("token")

    if not token:
        await require_token(update, context)
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_VISITS_COUNT,
                json={"patient_id": patient_id, "lang": lang},
                headers={"Authorization": f"Bearer {token}"}
            )

        data = await handle_api_response(response, context, update, lang)
        if data is False:
            return

        if not data or not any(any(d["closing"] for d in v["dates"]) for v in data.values()):
            await update.message.reply_text(
                TEXTS["no_discharges"][lang],
                reply_markup=keyboard_from_data(TEXTS["personal_menu"][lang])
            )
            return

        context.user_data["menu_state"] = "after_discharge"
        context.user_data["visits_data"] = data
        event_buttons = [[v["name"]] for v in data.values()]
        event_buttons.append([TEXTS["back_btn"][lang]])
        context.user_data["discharge_types_menu"] = event_buttons

        await update.message.reply_text(
            TEXTS["personal_data_prompt"][lang],
            reply_markup=keyboard_from_data(event_buttons)
        )

    except Exception as e:
        print("Ошибка:", e)
        await update.message.reply_text(TEXTS["api_response_error"][lang])


async def handle_discharge_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    selected_type_name = update.message.text
    visits_data = context.user_data.get("visits_data")

    if not visits_data:
        await update.message.reply_text(TEXTS["no_visits"][lang])
        return

    matching_type = next((v for v in visits_data.values() if v["name"] == selected_type_name), None)

    if not matching_type:
        await update.message.reply_text(TEXTS["no_visits"][lang])
        return

    context.user_data["selected_event_type"] = selected_type_name
    context.user_data["menu_state"] = "after_discharge_dates"
    context.user_data["current_visits_list"] = matching_type["dates"]

    date_buttons = [[d["incoming"]] for d in matching_type["dates"]]
    date_buttons.append([TEXTS["back_btn"][lang]])

    await update.message.reply_text(
        TEXTS["select_visit_date_prompt"][lang],
        reply_markup=keyboard_from_data(date_buttons)
    )


async def handle_discharge_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    selected_date = update.message.text
    visits = context.user_data.get("current_visits_list", [])
    visit_id = next((v["visit_id"] for v in visits if v["incoming"] == selected_date), None)

    if not visit_id:
        await update.message.reply_text(TEXTS["no_visits"][lang])
        return

    event_type = context.user_data.get("selected_event_type", "")
    kind = "extract" if "госпитализация" in event_type.lower() else "conclusion"
    token = context.user_data.get("token")

    if not token:
        await update.message.reply_text(TEXTS["unauthorized"][lang])
        return

    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{API_DOWNLOAD_PDF}/{visit_id}/{kind}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/pdf"
                },
                timeout=20.0
            )

        if response.status_code == 200:
            pdf_file = io.BytesIO(response.content)
            pdf_file.name = f"{kind}_{visit_id}.pdf"

            await update.message.reply_document(
                document=pdf_file,
                caption=TEXTS["file_sent"][lang]
            )
        else:
            print(f"API Error: {response.json().get('error', 'Unknown error')}")
            await update.message.reply_text(TEXTS["file_failed"][lang])

    except httpx.ReadTimeout:
        await update.message.reply_text("Время ожидания истекло. Попробуйте позже.")
    except Exception as e:
        print("Download error:", e)
        await update.message.reply_text(TEXTS["file_failed"][lang])
