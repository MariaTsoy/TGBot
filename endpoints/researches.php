<?php
require_once __DIR__ . '/../db.php';
require_once __DIR__ . '/../tokens.php';

header("Content-Type: application/json");

$data = json_decode(file_get_contents("php://input"), true);
$patient_id = $data["patient_id"] ?? null;
$auth_header = $_SERVER["HTTP_AUTHORIZATION"] ?? "";
$token = str_replace("Bearer ", "", $auth_header);

if (!$token || !$patient_id || !is_token_valid($token, $patient_id)) {
    http_response_code(401);
    echo json_encode(["error" => "Session expired or invalid token"]);
    exit;
}

$conn = connect_db();

$stmt = $conn->prepare("
    SELECT vst_incomingdate, IFNULL(vst_closingdate, CURDATE()) as vst_closingdate
    FROM hc_patient_visits
    WHERE vst_patientID = ? AND vst_eventtypeID IN (
        SELECT ID FROM hc_ref_eventtypes WHERE type_name LIKE '%госпитализация%'
    )
    ORDER BY vst_incomingdate DESC
    LIMIT 1
");
$stmt->bind_param("i", $patient_id);
$stmt->execute();
$result = $stmt->get_result()->fetch_assoc();

if (!$result) {
    echo json_encode(["error" => "no_hospitalization"]);
    exit;
}

$start = $result["vst_incomingdate"];
$end = $result["vst_closingdate"];

$stmt = $conn->prepare("
    SELECT r.date_sample, r.date_result, r.result_text, rr.rsch_name
    FROM hc_researches r
    JOIN hc_ref_researches rr ON r.refresearchID = rr.ID
    WHERE r.patientID = ? 
      AND r.date_sample BETWEEN ? AND ?
      AND r.contractorID != 100
      AND rr.rsch_show_in_patient_apps = 1
    ORDER BY r.date_sample DESC
");
$stmt->bind_param("iss", $patient_id, $start, $end);
$stmt->execute();
$rows = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);

$grouped = [];
foreach ($rows as $row) {
    $date = $row["date_sample"];
    if (!isset($grouped[$date])) $grouped[$date] = [];
    $grouped[$date][] = [
        "rsch_name" => $row["rsch_name"],
        "date_result" => $row["date_result"],
        "result_text" => $row["result_text"]
    ];
}

if (empty($rows)) {
    echo json_encode(["researches" => []]);
    exit;
}

$latest = array_slice(array_reverse($grouped), 0, 5, true);
$response = [];

foreach ($latest as $date => $items) {
    $response[] = ["date_sample" => $date, "items" => $items];
}

echo json_encode(["researches" => $response]);
$conn->close();
