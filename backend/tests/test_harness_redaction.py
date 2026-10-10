from app.harness_redaction import redact


def test_nested_secrets_and_pii():
    value = {'api_key': 'sk-testsecret', 'nested': [{'Password': 'hunter2', 'text': 'Email alice@example.com phone +1 (415) 555-2671 token Bearer abc.def.xyz'}]}
    clean = redact(value)
    assert clean['api_key'] == '[REDACTED]'
    assert clean['nested'][0]['Password'] == '[REDACTED]'
    assert all(x not in str(clean) for x in ['alice@example.com', '555-2671', 'abc.def.xyz'])
    assert value['api_key'] == 'sk-testsecret'


def test_embedded_credentials_and_private_key():
    text = 'password=hunter2 https://user:secret@example.com sk-abcdefghijklmno -----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----'
    assert all(x not in redact(text) for x in ['hunter2', 'secret', 'sk-abcdefghijklmno'])


def test_raw_json_and_quoted_spaced_passwords():
    source = '{"token": "very secret token", "password": "two word password", "ok": "safe"}'
    cleaned = redact(source)
    assert all(part not in cleaned for part in ['very secret token', 'two word password'])
    assert 'safe' in cleaned
    assert 'two word password' not in redact('PASSWORD="two word password"')


def test_incomplete_private_key_is_redacted_to_end():
    source = 'diagnostic -----BEGIN PRIVATE KEY-----\nvery sensitive key material'
    assert redact(source) == 'diagnostic [REDACTED]'


def test_raw_json_compound_credential_keys_match_mapping_redaction():
    import json
    fields = {'access_token': 'opaque-access-value', 'refresh_token': 'opaque-refresh-value', 'client_secret': 'opaque-client-value', 'oauthToken': 'opaque-oauth-value', 'authorization': 'opaque-auth-value', 'sessionCookie': 'opaque-cookie-value', 'private_key': 'opaque-private-value'}
    clean = redact(json.dumps(fields))
    assert all(value not in clean for value in fields.values())
    assert all(value == '[REDACTED]' for value in redact(fields).values())
