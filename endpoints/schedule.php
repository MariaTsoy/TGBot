<?php
require_once __DIR__ . '/../db.php';
require_once __DIR__ . '/../tokens.php';

header("Content-Type: application/json");

$data = json_decode(file_get_contents("php://input"), true);
$patient_id = $data["patient_id"] ?? null;
$lang = $data["lang"] ?? "ru";

$auth_header = $_SERVER["HTTP_AUTHORIZATION"] ?? "";
$token = str_replace("Bearer ", "", $auth_header);

if (!$token || !$patient_id || !is_token_valid($token, $patient_id)) {
    http_response_code(401);
    echo json_encode(["error" => "Session expired or invalid token"]);
    exit;
}

$name_column = match ($lang) {
    "kz" => "et.type_name_kz",
    "en" => "et.type_name_en",
    default => "et.type_name"
};

$conn = connect_db();

$query = "
    SELECT 
        sp.schp_date,
        sp.schp_time,
        d.dpr_shortname AS department,
        $name_column AS event_type,
        u.usr_lname,
        u.usr_gname,
        u.usr_mname
    FROM hc_schedule_planning sp
    LEFT JOIN hc_ref_departments d ON sp.schp_departmentID = d.ID
    LEFT JOIN hc_ref_eventtypes et ON sp.schp_eventtypeID = et.ID
    LEFT JOIN hc_users u ON sp.schp_doctorID = u.ID
    WHERE sp.schp_patientID = ?
    ORDER BY sp.schp_date, sp.schp_time
";

$stmt = $conn->prepare($query);
$stmt->bind_param("i", $patient_id);
$stmt->execute();
$result = $stmt->get_result();

$records = [];
while ($row = $result->fetch_assoc()) {
    if (isset($row["schp_time"])) {
        $seconds = is_numeric($row["schp_time"]) ? (int)$row["schp_time"] : strtotime($row["schp_time"]) % 86400;
        $row["schp_time"] = sprintf("%02d:%02d", $seconds / 3600, ($seconds % 3600) / 60);
    }

    if (isset($row["schp_date"])) {
        $row["schp_date"] = date("d.m.Y", strtotime($row["schp_date"]));
    }

    $row["doctor_name"] = implode(" ", array_filter([$row["usr_lname"], $row["usr_gname"], $row["usr_mname"]])) ?: "—";

    $records[] = $row;
}

$stmt->close();
$conn->close();

echo json_encode(["records" => $records]);
