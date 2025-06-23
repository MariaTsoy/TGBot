<?php
require_once __DIR__ . '/../db.php';
require_once __DIR__ . '/../tokens.php';

header("Content-Type: application/json");

$data = json_decode(file_get_contents("php://input"), true);
$visit_id = $data["visit_id"] ?? null;
$date_filter = $data["date"] ?? null;
$patient_id = $data["patient_id"] ?? null;

$auth_header = $_SERVER["HTTP_AUTHORIZATION"] ?? "";
$token = str_replace("Bearer ", "", $auth_header);

if (!$token || !$patient_id || !is_token_valid($token, $patient_id)) {
    http_response_code(401);
    echo json_encode(["error" => "Session expired or invalid token"]);
    exit;
}

if (!$visit_id || !$date_filter) {
    http_response_code(400);
    echo json_encode(["error" => "Missing visit_id or date"]);
    exit;
}

$target_date = date("Y-m-d");
if ($date_filter === "yesterday") {
    $target_date = date("Y-m-d", strtotime("-1 day"));
}

$conn = connect_db();

// Temp
$temp_stmt = $conn->prepare("SELECT log_time, log_value FROM hc_visit_logtemp WHERE log_visitID = ? AND log_date = ?");
$temp_stmt->bind_param("is", $visit_id, $target_date);
$temp_stmt->execute();
$temp_result = $temp_stmt->get_result();
$temperature = $temp_result->fetch_all(MYSQLI_ASSOC);
$temp_stmt->close();

// Saturation
$sat_stmt = $conn->prepare("SELECT log_time, log_value FROM hc_visit_logsaturation WHERE log_visitID = ? AND log_date = ?");
$sat_stmt->bind_param("is", $visit_id, $target_date);
$sat_stmt->execute();
$sat_result = $sat_stmt->get_result();
$saturation = $sat_result->fetch_all(MYSQLI_ASSOC);
$sat_stmt->close();

// Pressure
$press_stmt = $conn->prepare("SELECT log_time, log_up, log_low, log_pulse FROM hc_visit_logpressure WHERE log_visitID = ? AND log_date = ?");
$press_stmt->bind_param("is", $visit_id, $target_date);
$press_stmt->execute();
$press_result = $press_stmt->get_result();
$pressure = $press_result->fetch_all(MYSQLI_ASSOC);
$press_stmt->close();

$conn->close();

function format_time(&$array, $field = "log_time") {
    foreach ($array as &$item) {
        if (isset($item[$field])) {
            $seconds = is_numeric($item[$field]) ? (int)$item[$field] : strtotime($item[$field]) % 86400;
            $item[$field] = sprintf("%02d:%02d", $seconds / 3600, ($seconds % 3600) / 60);
        }
    }
}

format_time($temperature);
format_time($saturation);
format_time($pressure);

echo json_encode([
    "temperature" => $temperature,
    "saturation" => $saturation,
    "pressure" => $pressure
]);
