"""Credential format compatibility without making any network requests."""
import pytest
from database.supabase_client import SupabaseRestClient, _resolve_supabase_key


@pytest.mark.parametrize('key,has_bearer', [
    ('legacy-placeholder', True),
    ('sb_secret_test-placeholder', False),
    ('sb_publishable_test-placeholder', False),
])
def test_opaque_api_keys_are_not_sent_as_jwts(key, has_bearer):
    client = SupabaseRestClient('https://example.supabase.co', key)
    try:
        assert client.headers['apikey'] == key
        assert ('Authorization' in client.headers) is has_bearer
        if has_bearer:
            assert client.headers['Authorization'] == 'Bearer '+key
        else:
            assert 'authorization' not in client._http.headers
    finally:
        client.close()


def test_secret_key_override_and_legacy_fallbacks(monkeypatch):
    monkeypatch.setenv('SUPABASE_KEY', 'anon-placeholder')
    monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY', 'role-placeholder')
    monkeypatch.setenv('SUPABASE_SECRET_KEY', 'sb_secret_test-placeholder')
    assert _resolve_supabase_key() == 'sb_secret_test-placeholder'
    monkeypatch.delenv('SUPABASE_SECRET_KEY')
    assert _resolve_supabase_key() == 'role-placeholder'
    monkeypatch.delenv('SUPABASE_SERVICE_ROLE_KEY')
    assert _resolve_supabase_key() == 'anon-placeholder'
