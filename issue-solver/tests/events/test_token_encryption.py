import os
import pytest
from datetime import datetime
from unittest.mock import patch

from issue_solver.events.domain import CodeRepositoryConnected
from issue_solver.events.serializable_records import (
    CodeRepositoryConnectedRecord,
    _encrypt_token,
    _decrypt_token,
    serialize,
)


@pytest.fixture
def sample_event():
    """Create a sample CodeRepositoryConnected event for testing."""
    return CodeRepositoryConnected(
        occurred_at=datetime(2023, 1, 1, 10, 0, 0),
        url="https://github.com/test/repo",
        access_token="ghp_test123456789",
        user_id="test-user",
        space_id="test-space",
        knowledge_base_id="kb-123",
        process_id="proc-123",
    )


@pytest.fixture
def encryption_key():
    """Provide a test encryption key."""
    return "hp6ocOWdpR69r8lRUzci2cCSjwmqpntBojmnhaIJD_M="


def test_encrypt_decrypt_with_key(encryption_key):
    """Test encryption and decryption when key is available."""
    token = "ghp_test123456789"

    with patch.dict(os.environ, {"TOKEN_ENCRYPTION_KEY": encryption_key}):
        encrypted = _encrypt_token(token)
        decrypted = _decrypt_token(encrypted)

    # Token should be encrypted (different from original)
    assert encrypted != token
    assert len(encrypted) > len(token)

    # Decryption should return original token
    assert decrypted == token


def test_encrypt_decrypt_without_key():
    """Test encryption and decryption when no key is available."""
    token = "ghp_test123456789"

    with patch.dict(os.environ, {}, clear=True):
        encrypted = _encrypt_token(token)
        decrypted = _decrypt_token(encrypted)

    # Without key, token should remain unchanged
    assert encrypted == token
    assert decrypted == token


def test_encrypt_empty_token(encryption_key):
    """Test encryption of empty token."""
    with patch.dict(os.environ, {"TOKEN_ENCRYPTION_KEY": encryption_key}):
        encrypted = _encrypt_token("")
        decrypted = _decrypt_token("")

    assert encrypted == ""
    assert decrypted == ""


def test_decrypt_invalid_token_falls_back(encryption_key):
    """Test that decryption falls back gracefully for invalid encrypted tokens."""
    invalid_encrypted = "invalid_encrypted_token"

    with patch.dict(os.environ, {"TOKEN_ENCRYPTION_KEY": encryption_key}):
        result = _decrypt_token(invalid_encrypted)

    # Should fall back to returning the original string
    assert result == invalid_encrypted


def test_record_creation_with_encryption(sample_event, encryption_key):
    """Test that creating a record encrypts the token."""
    with patch.dict(os.environ, {"TOKEN_ENCRYPTION_KEY": encryption_key}):
        record = CodeRepositoryConnectedRecord.create_from(sample_event)

    # Token should be encrypted in the record
    assert record.access_token != sample_event.access_token
    assert len(record.access_token) > len(sample_event.access_token)


def test_record_creation_without_encryption(sample_event):
    """Test that creating a record without key keeps token as is."""
    with patch.dict(os.environ, {}, clear=True):
        record = CodeRepositoryConnectedRecord.create_from(sample_event)

    # Token should remain unchanged
    assert record.access_token == sample_event.access_token


def test_to_domain_event_decrypts_token(sample_event, encryption_key):
    """Test that converting back to domain event decrypts the token."""
    with patch.dict(os.environ, {"TOKEN_ENCRYPTION_KEY": encryption_key}):
        record = CodeRepositoryConnectedRecord.create_from(sample_event)
        restored_event = record.to_domain_event()

    # Original and restored event should have the same token
    assert restored_event.access_token == sample_event.access_token


def test_serialize_function_with_encryption(sample_event, encryption_key):
    """Test the serialize function with encryption."""
    with patch.dict(os.environ, {"TOKEN_ENCRYPTION_KEY": encryption_key}):
        record = serialize(sample_event)

        assert isinstance(record, CodeRepositoryConnectedRecord)
        assert record.access_token != sample_event.access_token

        # Verify round-trip - decryption also needs the key
        restored_event = record.to_domain_event()
        assert restored_event.access_token == sample_event.access_token


def test_backward_compatibility_mixed_tokens(encryption_key):
    """Test backward compatibility with mixed encrypted and plain tokens."""
    plain_token = "ghp_plain123"

    with patch.dict(os.environ, {"TOKEN_ENCRYPTION_KEY": encryption_key}):
        # Encrypt a token
        encrypted_token = _encrypt_token("ghp_encrypted123")

        # Both should decrypt correctly
        assert _decrypt_token(plain_token) == plain_token  # Plain token unchanged
        assert (
            _decrypt_token(encrypted_token) == "ghp_encrypted123"
        )  # Encrypted token decrypted


def test_different_keys_produce_different_encryption():
    """Test that different keys produce different encrypted results."""
    token = "ghp_test123456789"
    key1 = "hp6ocOWdpR69r8lRUzci2cCSjwmqpntBojmnhaIJD_M="
    key2 = "PCUnDxMCDOYyIM-NOU80eGgShte3MSZFwmkN0esk360="

    with patch.dict(os.environ, {"TOKEN_ENCRYPTION_KEY": key1}):
        encrypted1 = _encrypt_token(token)

    with patch.dict(os.environ, {"TOKEN_ENCRYPTION_KEY": key2}):
        encrypted2 = _encrypt_token(token)

    # Different keys should produce different encrypted values
    assert encrypted1 != encrypted2
    assert encrypted1 != token
    assert encrypted2 != token
