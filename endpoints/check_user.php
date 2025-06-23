<?php
require_once __DIR__ . '/../db.php';
require_once __DIR__ . '/../tokens.php';

header("Content-Type: application/json");

$data = json_decode(file_get_contents("php://input"), true);
$phone = $data["phone"] ?? "";

if (!$phone) {
    http_response_code(400);
    echo json_encode(["error" => "Missing phone number"]);
    exit;
}

$conn = connect_db();

$cleaned_phone = preg_replace("/[\s\-\+\(\)]/", "", $phone);

$stmt = $conn->prepare("
    SELECT id, ptn_lname, ptn_gname, ptn_mname, ptn_preflang
    FROM hc_patients
    WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(ptn_mobile, ' ', ''), '-', ''), '(', ''), ')', ''), '+', '') = ?
");
$stmt->bind_param("s", $cleaned_phone);
$stmt->execute();
$result = $stmt->get_result()->fetch_assoc();

if ($result) {
    $token_data = generate_token($result["id"]);
    echo json_encode([
        "found" => true,
        "data" => $result,
        "token" => $token_data["token"]
    ]);
} else {
    echo json_encode(["found" => false]);
}

$stmt->close();
$conn->close();
