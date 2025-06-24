<?php
require_once __DIR__ . '/../db.php';
require_once __DIR__ . '/../tokens.php';

header("Content-Type: application/json");

$data = json_decode(file_get_contents("php://input"), true);
$telegram_id = $data["telegram_id"] ?? null;

if (!$telegram_id) {
    http_response_code(400);
    echo json_encode(["error" => "Missing Telegram ID"]);
    exit;
}

$tokens = json_decode(file_get_contents(__DIR__ . '/../tokens.json'), true);

foreach ($tokens as $token => $info) {
    if (isset($info["telegram_id"]) && $info["telegram_id"] == $telegram_id) {
        $conn = connect_db();
        $stmt = $conn->prepare("SELECT id, ptn_lname, ptn_gname, ptn_mname, ptn_mobile, ptn_preflang FROM hc_patients WHERE id = ?");
        $stmt->bind_param("i", $info["patient_id"]);
        $stmt->execute();
        $result = $stmt->get_result()->fetch_assoc();
        $stmt->close();
        $conn->close();

        if ($result) {
            echo json_encode([
                "found" => true,
                "token" => $token,
                "data" => $result
            ]);
            exit;
        }
    }
}

echo json_encode(["found" => false]);
