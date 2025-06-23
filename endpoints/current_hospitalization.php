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
    SELECT v.ID AS visit_id
    FROM hc_patient_visits v
    JOIN hc_ref_eventtypes r ON v.vst_eventtypeID = r.ID
    WHERE v.vst_patientID = ? AND v.vst_closingdate IS NULL AND r.type_name LIKE '%госпитализация%'
    LIMIT 1
");

$stmt->bind_param("i", $patient_id);
$stmt->execute();
$result = $stmt->get_result()->fetch_assoc();

if ($result) {
    echo json_encode(["active" => true, "visit_id" => $result["visit_id"]]);
} else {
    echo json_encode(["active" => false]);
}

$stmt->close();
$conn->close();
