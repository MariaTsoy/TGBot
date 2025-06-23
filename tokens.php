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

function generate_token($patient_id) {
    $tokens = load_tokens();
    $token = bin2hex(random_bytes(16));
    $expires_at = (new DateTime())->modify('+30 minutes')->format(DateTime::ATOM);
    $tokens[$token] = [
        "patient_id" => $patient_id,
        "expires_at" => $expires_at
    ];
    save_tokens($tokens);
    return ["token" => $token, "expires_at" => $expires_at];
}

function is_token_valid($token, $patient_id) {
    $tokens = load_tokens();
    if (!isset($tokens[$token])) return false;

    $data = $tokens[$token];
    if ((int)$data["patient_id"] !== (int)$patient_id) return false;

    $now = new DateTime();
    $expiry = DateTime::createFromFormat(DateTime::ATOM, $data["expires_at"]);
    if ($expiry < $now) return false;

    return true;
}
