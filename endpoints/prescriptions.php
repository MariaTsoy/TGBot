<?php
require_once __DIR__ . '/../db.php';
require_once __DIR__ . '/../tokens.php';

header("Content-Type: application/json");

$data = json_decode(file_get_contents("php://input"), true);
$patient_id = $data["patient_id"] ?? null;
$visit_id = $data["visit_id"] ?? null;
$date_filter = $data["date"] ?? null;

$auth_header = $_SERVER["HTTP_AUTHORIZATION"] ?? "";
$token = str_replace("Bearer ", "", $auth_header);

if (!$token || !$patient_id || !is_token_valid($token, $patient_id)) {
    http_response_code(401);
    echo json_encode(["error" => "Session expired or invalid token"]);
    exit;
}

if (!$visit_id || !$date_filter) {
    http_response_code(400);
    echo json_encode(["error" => "Missing data"]);
    exit;
}

$target_date = date("Y-m-d");
if ($date_filter === "yesterday") {
    $target_date = date("Y-m-d", strtotime("-1 day"));
}

$conn = connect_db();

$stmt = $conn->prepare("
    SELECT ass_time, ass_remarks, ass_delivered
    FROM hc_assigns
    WHERE ass_visitID = ? AND ass_canceled = 0 AND ass_date = ?
    ORDER BY ass_time
");
$stmt->bind_param("is", $visit_id, $target_date);
$stmt->execute();
$result = $stmt->get_result();

$rows = [];
while ($row = $result->fetch_assoc()) {
    // Преобразуем ass_time в строку (если это время)
    if ($row["ass_time"] instanceof DateTime || $row["ass_time"] instanceof \DateInterval) {
        $row["ass_time"] = (string)$row["ass_time"];
    }
    $rows[] = $row;
}

echo json_encode($rows);

$stmt->close();
$conn->close();
