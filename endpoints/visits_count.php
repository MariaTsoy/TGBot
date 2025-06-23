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

if ($lang === "kz") {
    $name_column = "type_name_kz";
} elseif ($lang === "en") {
    $name_column = "type_name_en";
} else {
    $name_column = "type_name";
}


$conn = connect_db();

$stmt = $conn->prepare("
    SELECT 
        v.ID AS visit_id,
        v.vst_eventtypeID, 
        r.$name_column AS event_name,
        v.vst_incomingdate, 
        v.vst_closingdate
    FROM hc_patient_visits v
    LEFT JOIN hc_ref_eventtypes r ON v.vst_eventtypeID = r.ID
    WHERE v.vst_patientID = ?
      AND v.vst_eventtypeID NOT IN (7, 8)
    ORDER BY v.vst_eventtypeID, v.vst_incomingdate
");

$stmt->bind_param("i", $patient_id);
$stmt->execute();
$result = $stmt->get_result();

$grouped = [];

while ($row = $result->fetch_assoc()) {
    $event_type = $row["vst_eventtypeID"];
    $event_name = $row["event_name"] ?? "Тип $event_type";
    $incoming = $row["vst_incomingdate"];
    $closing = $row["vst_closingdate"];

    if (!isset($grouped[$event_type])) {
        $grouped[$event_type] = [
            "count" => 0,
            "name" => $event_name,
            "dates" => []
        ];
    }

    $grouped[$event_type]["count"] += 1;
    $grouped[$event_type]["dates"][] = [
        "visit_id" => $row["visit_id"],
        "incoming" => $incoming ? date("d.m.Y", strtotime($incoming)) : null,
        "closing" => $closing ? date("d.m.Y", strtotime($closing)) : null
    ];
}

echo json_encode($grouped);

$stmt->close();
$conn->close();
