from flask import Flask, request, jsonify
import mysql.connector, secrets
from dotenv import load_dotenv
from datetime import datetime, timedelta

from flask import send_file
import requests
from io import BytesIO


load_dotenv()

app = Flask(__name__)

active_tokens = {}

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "hem",
}


try:
    conn = mysql.connector.connect(**db_config)
    print("Успешно подключено к базе данных")
except Exception as e:
    print(f"Ошибка подключения к базе данных: {e}")


def is_token_valid(token, patient_id):

    print(token, patient_id, active_tokens.get(token))

    token_data = active_tokens.get(token)
    if not token_data:
        return False
    try:
        if int(token_data["patient_id"]) != int(patient_id):
            return False
    except:
        return False
    if datetime.utcnow() > token_data["expires_at"]:
        return False
    return True


@app.route("/check_user", methods=["POST"])
def check_user():
    data = request.get_json()
    phone = data.get("phone")

    if not phone:
        return jsonify({"error": "Missing phone number"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, ptn_lname, ptn_gname, ptn_mname, ptn_preflang
        FROM hc_patients
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(ptn_mobile, ' ', ''), '-', ''), '(', ''), ')', ''), '+', '') = %s
        """

        cleaned_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
        cursor.execute(query, (cleaned_phone,))
        result = cursor.fetchone()

        if result:
            token = secrets.token_hex(16)
            expires_at = datetime.utcnow() + timedelta(minutes=30)
            active_tokens[token] = {"patient_id": result["id"], "expires_at": expires_at}

            return jsonify({
                "found": True,
                "data": result,
                "token": token
            })
        else:
            return jsonify({"found": False})

    except Exception as e:
        print("Ошибка при запросе к БД:", e)
        return jsonify({"error": "Database error"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/visits_count", methods=["POST"])
def visits_count():
    data = request.get_json()
    patient_id = data.get("patient_id")
    lang = data.get("lang", "ru")
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    if not token or not is_token_valid(token, patient_id):
        return jsonify({"error": "Session expired or invalid token"}), 401
    if not patient_id:
        return jsonify({"error": "Missing patient_id"}), 400

    name_column = {
        "ru": "type_name",
        "kz": "type_name_kz",
        "en": "type_name_en"
    }.get(lang, "type_name")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = f"""
        SELECT 
            v.ID AS visit_id,
            v.vst_eventtypeID, 
            r.{name_column} AS event_name,
            v.vst_incomingdate, 
            v.vst_closingdate
        FROM hc_patient_visits v
        LEFT JOIN hc_ref_eventtypes r ON v.vst_eventtypeID = r.ID
        WHERE v.vst_patientID = %s AND v.vst_eventtypeID NOT IN (7, 8)
        ORDER BY v.vst_eventtypeID, v.vst_incomingdate
        """

        cursor.execute(query, (patient_id,))
        results = cursor.fetchall()

        grouped = {}
        for row in results:
            event_type = row["vst_eventtypeID"]
            event_name = row["event_name"] or f"Тип {event_type}"  # на случай, если нет названия
            incoming = row["vst_incomingdate"]
            closing = row["vst_closingdate"]

            if event_type not in grouped:
                grouped[event_type] = {
                    "count": 0,
                    "name": event_name,
                    "dates": []
                }
            grouped[event_type]["count"] += 1
            grouped[event_type]["dates"].append({
                "visit_id": row["visit_id"],
                "incoming": incoming.strftime("%d.%m.%Y") if incoming else None,
                "closing": closing.strftime("%d.%m.%Y") if closing else None
            })
        return jsonify(grouped)

    except Exception as e:
        print("Ошибка при запросе к БД:", e)
        return jsonify({"error": "Database error"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/current_hospitalization", methods=["POST"])
def current_hospitalization():
    data = request.get_json()
    patient_id = data.get("patient_id")
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    if not token or not is_token_valid(token, patient_id):
        return jsonify({"error": "Session expired or invalid token"}), 401

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT v.ID AS visit_id
        FROM hc_patient_visits v
        JOIN hc_ref_eventtypes r ON v.vst_eventtypeID = r.ID
        WHERE v.vst_patientID = %s AND v.vst_closingdate IS NULL AND r.type_name LIKE '%госпитализация%'
        LIMIT 1
        """
        cursor.execute(query, (patient_id,))
        result = cursor.fetchone()

        if result:
            return jsonify({"active": True, "visit_id": result["visit_id"]})
        else:
            return jsonify({"active": False})

    except Exception as e:
        print("Ошибка при проверке госпитализации:", e)
        return jsonify({"error": "Database error"}), 500
    finally:
        cursor.close()
        conn.close()



@app.route("/prescriptions", methods=["POST"])
def get_prescriptions():
    data = request.get_json()
    patient_id = data.get("patient_id")
    visit_id = data.get("visit_id")
    date_filter = data.get("date")
    auth_header = request.headers.get("Authorization", "")

    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None
    if not token or not is_token_valid(token, patient_id):
        return jsonify({"error": "Session expired or invalid token"}), 401

    if not visit_id or not date_filter:
        return jsonify({"error": "Missing data"}), 400

    if date_filter == "today":
        target_date = datetime.now().strftime("%Y-%m-%d")
    else:
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT ass_time, ass_remarks, ass_delivered
        FROM hc_assigns
        WHERE ass_visitID = %s
          AND ass_canceled = 0
          AND ass_date = %s
        ORDER BY ass_time
        """
        cursor.execute(query, (visit_id, target_date))
        results = cursor.fetchall()

        for row in results:
            if isinstance(row["ass_time"], (datetime, timedelta)):
                row["ass_time"] = str(row["ass_time"])

        return jsonify(results)

    except Exception as e:
        print("Ошибка при получении назначений:", e)
        return jsonify({"error": "Database error"}), 500
    finally:
        cursor.close()
        conn.close()



@app.route("/vitals", methods=["POST"])
def get_vitals():
    data = request.get_json()
    visit_id = data.get("visit_id")
    date_filter = data.get("date")  # "today" / "yesterday"
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    if not token or not is_token_valid(token, data.get("patient_id")):
        return jsonify({"error": "Session expired or invalid token"}), 401

    if not visit_id or not date_filter:
        return jsonify({"error": "Missing visit_id or date"}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        if date_filter == "yesterday":
            date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        vitals = {
            "temperature": [],
            "saturation": [],
            "pressure": []
        }
        cursor.execute("""
            SELECT log_time, log_value FROM hc_visit_logtemp
            WHERE log_visitID = %s AND log_date = %s
        """, (visit_id, date_str))
        vitals["temperature"] = cursor.fetchall()
        cursor.execute("""
            SELECT log_time, log_value FROM hc_visit_logsaturation
            WHERE log_visitID = %s AND log_date = %s
        """, (visit_id, date_str))
        vitals["saturation"] = cursor.fetchall()
        cursor.execute("""
            SELECT log_time, log_up, log_low, log_pulse FROM hc_visit_logpressure
            WHERE log_visitID = %s AND log_date = %s
        """, (visit_id, date_str))
        vitals["pressure"] = cursor.fetchall()

        for t in vitals["temperature"]:
            if isinstance(t["log_time"], timedelta):
                seconds = t["log_time"].total_seconds()
                t["log_time"] = f"{int(seconds // 3600):02}:{int((seconds % 3600) // 60):02}"
        for s in vitals["saturation"]:
            if isinstance(s["log_time"], timedelta):
                seconds = s["log_time"].total_seconds()
                s["log_time"] = f"{int(seconds // 3600):02}:{int((seconds % 3600) // 60):02}"
        for p in vitals["pressure"]:
            if isinstance(p["log_time"], timedelta):
                seconds = p["log_time"].total_seconds()
                p["log_time"] = f"{int(seconds // 3600):02}:{int((seconds % 3600) // 60):02}"

        return jsonify(vitals)

    except Exception as e:
        print("Ошибка при получении показателей:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@app.route("/schedule", methods=["POST"])
def get_schedule():
    data = request.get_json()
    patient_id = data.get("patient_id")
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if not token or not is_token_valid(token, patient_id):
        return jsonify({"error": "Session expired or invalid token"}), 401

    lang = data.get("lang", "ru")
    type_name_col = {
        "ru": "et.type_name",
        "kz": "et.type_name_kz",
        "en": "et.type_name_en"
    }.get(lang, "et.type_name")

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = f"""
            SELECT 
                sp.schp_date, sp.schp_time,
                d.dpr_shortname AS department,
                {type_name_col} AS event_type,
                u.usr_lname, u.usr_gname, u.usr_mname
            FROM hc_schedule_planning sp
            LEFT JOIN hc_ref_departments d ON sp.schp_departmentID = d.ID
            LEFT JOIN hc_ref_eventtypes et ON sp.schp_eventtypeID = et.ID
            LEFT JOIN hc_users u ON sp.schp_doctorID = u.ID
            WHERE sp.schp_patientID = %s
            ORDER BY sp.schp_date, sp.schp_time
        """
        cursor.execute(query, (patient_id,))
        results = cursor.fetchall()

        for row in results:
            if isinstance(row["schp_time"], (datetime, timedelta)):
                seconds = int(row["schp_time"].total_seconds())
                row["schp_time"] = f"{seconds // 3600:02}:{(seconds % 3600) // 60:02}"
            row["schp_date"] = row["schp_date"].strftime("%d.%m.%Y")

            fio = " ".join(filter(None, [row["usr_lname"], row["usr_gname"], row["usr_mname"]]))
            row["doctor_name"] = fio or "—"

        return jsonify({"records": results})

    except Exception as e:
        print("Ошибка при получении записей:", e)
        return jsonify({"error": "Database error"}), 500
    finally:
        cursor.close()
        conn.close()




@app.route("/get_file_link", methods=["POST"])
def get_file_link():
    data = request.get_json()

    patient_id = data.get("patient_id")
    visit_id = data.get("visit_id")
    event_type = data.get("event_type", "").lower()

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    if not token or not is_token_valid(token, patient_id):
        return jsonify({"error": "Session expired or invalid token"}), 401

    if not patient_id:
        return jsonify({"error": "Missing patient_id"}), 400

    if not visit_id:
        return jsonify({"error": "Missing visit_id"}), 400

    if "госпитализация" in event_type:
        file_url = f"https://127.0.0.1:5000/visits/fileextract/{visit_id}"
    else:
        file_url = f"https://127.0.0.1:5000/ambulance/getconclusionpdf/{visit_id}"
    return jsonify({"file_url": file_url})



@app.route("/download_pdf/<int:visit_id>/<string:kind>", methods=["GET"])
def download_pdf(visit_id, kind):
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing authorization"}), 401

        if kind == "extract":
            source_url = f"https://localhost/visits/fileextract/{visit_id}"
        else:
            source_url = f"https://localhost/ambulance/getconclusionpdf/{visit_id}"

        cookies = {
            'session_token': 'your_session_token_here'  # Замените на реальный токен
        }
        headers = {
            "Authorization": auth_header,
            "Accept": "application/pdf",
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            source_url,
            verify=False,
            headers=headers,
            cookies=cookies,
            allow_redirects=False,
            timeout=10
        )
        if 300 <= response.status_code < 400:
            return jsonify({
                "error": "Authentication required",
                "redirect_url": response.headers.get("Location")
            }), 401

        if response.status_code != 200:
            return jsonify({
                "error": f"PDF server returned {response.status_code}",
                "content_type": response.headers.get("Content-Type"),
                "content_sample": response.text[:200]  # Для отладки
            }), 500

        content_type = response.headers.get("Content-Type", "").lower()
        if "application/pdf" not in content_type:
            return jsonify({
                "error": f"Expected PDF, got {content_type}",
                "content_sample": response.text[:200]  # Для отладки
            }), 500

        return send_file(
            BytesIO(response.content),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{kind}_{visit_id}.pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True, port=5000)
