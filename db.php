<?php
function connect_db() {
    $host = "localhost";
    $user = "root";
    $password = "";
    $database = "hem";

    $conn = new mysqli($host, $user, $password, $database);
    if ($conn->connect_error) {
        http_response_code(500);
        echo json_encode(["error" => "DB connection failed: " . $conn->connect_error]);
        exit;
    }

    return $conn;
}
