<?php
$request_uri = parse_url($_SERVER["REQUEST_URI"], PHP_URL_PATH);
$method = $_SERVER["REQUEST_METHOD"];

$routes = [
    "/check_telegram" => "endpoints/check_telegram.php",
    "/check_user" => "endpoints/check_user.php",
    "/visits_count" => "endpoints/visits_count.php",
    "/current_hospitalization" => "endpoints/current_hospitalization.php",
    "/prescriptions" => "endpoints/prescriptions.php",
    "/vitals" => "endpoints/vitals.php",
    "/schedule" => "endpoints/schedule.php"
];

if ($method === "POST" && isset($routes[$request_uri])) {
    require $routes[$request_uri];
} else {
    http_response_code(404);
    echo json_encode(["error" => "Not Found"]);
}
