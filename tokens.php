<?php

define("TOKEN_FILE", __DIR__ . "/tokens.json");


function load_tokens() {
    if (!file_exists(TOKEN_FILE)) return [];
    $json = file_get_contents(TOKEN_FILE);
    return json_decode($json, true) ?: [];
}


function save_tokens($tokens) {
    file_put_contents(TOKEN_FILE, json_encode($tokens, JSON_PRETTY_PRINT));
}


function generate_token($patient_id, $telegram_id = null) {
    $tokens = json_decode(file_get_contents(__DIR__ . '/tokens.json'), true) ?? [];

    foreach ($tokens as $token => $data) {
        if (isset($data["telegram_id"]) && $data["telegram_id"] == $telegram_id) {
            return ["token" => $token];
        }
    }

    $token = bin2hex(random_bytes(32));
    $tokens[$token] = [
        "patient_id" => $patient_id,
        "created_at" => time(),
        "telegram_id" => $telegram_id
    ];
    file_put_contents(__DIR__ . '/tokens.json', json_encode($tokens, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    return ["token" => $token];
}


function is_token_valid($token, $patient_id) {
    $tokens = load_tokens();
    if (!isset($tokens[$token])) return false;

    $data = $tokens[$token];
    if ((int)$data["patient_id"] !== (int)$patient_id) return false;

    return true;
}
