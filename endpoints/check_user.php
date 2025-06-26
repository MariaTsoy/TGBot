<?php
require_once __DIR__ . '/../db.php';
require_once __DIR__ . '/../tokens.php';

header("Content-Type: application/json");

$data = json_decode(file_get_contents("php://input"), true);
$phone = $data["phone"] ?? "";
$iin = $data["iin"] ?? "";
$telegram_id = $data["telegram_id"] ?? "";

if (!$phone) {
    http_response_code(400);
    echo json_encode(["error" => "Missing phone number"]);
    exit;
}

$conn = connect_db();
$cleaned_phone = preg_replace("/[\s\-\+\(\)]/", "", $phone);

$stmt = $conn->prepare("
    SELECT id, ptn_lname, ptn_gname, ptn_mname, ptn_preflang, ptn_mobile
    FROM hc_patients
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(ptn_mobile, ' ', ''), '-', ''), '(', ''), ')', ''), '+', '') = ?
      AND ptn_iin = ?
");
$stmt->bind_param("ss", $cleaned_phone, $iin);
$stmt->execute();
$result = $stmt->get_result()->fetch_assoc();
$stmt->close();

if ($result) {
    $token_data = generate_token($result["id"], $telegram_id);
    echo json_encode([
        "found" => true,
        "data" => $result,
        "token" => $token_data["token"]
    ]);
} else {
    $stmt_phone = $conn->prepare("
        SELECT id FROM hc_patients
        WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(ptn_mobile, ' ', ''), '-', ''), '(', ''), ')', ''), '+', '') = ?
    ");
    $stmt_phone->bind_param("s", $cleaned_phone);
    $stmt_phone->execute();
    $phone_check = $stmt_phone->get_result()->fetch_assoc();
    $stmt_phone->close();

    if ($phone_check) {
        echo json_encode(["found" => false, "error" => "wrong_iin"]);
    } else {
        echo json_encode(["found" => false, "error" => "not_found"]);
    }
}

$conn->close();
