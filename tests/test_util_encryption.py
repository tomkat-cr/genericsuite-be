"""
Tests for genericsuite/util/encryption.py — encrypt/decrypt strings.
"""
import base64

from cryptography.fernet import Fernet, InvalidToken
from genericsuite.util.encryption import encrypt_string, decrypt_string


def _make_seed() -> str:
    """Generate a valid Fernet key (URL-safe base64, 32 bytes)."""
    return Fernet.generate_key().decode()


def test_round_trip_encryption():
    seed = _make_seed()
    plaintext = "hello, world!"
    ciphertext = encrypt_string(seed, plaintext)
    assert decrypt_string(seed, ciphertext) == plaintext


def test_ciphertext_differs_from_plaintext():
    seed = _make_seed()
    plaintext = "sensitive data"
    ciphertext = encrypt_string(seed, plaintext)
    assert ciphertext != plaintext


def test_different_encryptions_of_same_value_differ():
    """Fernet uses random IV so two encryptions of the same value differ."""
    seed = _make_seed()
    c1 = encrypt_string(seed, "value")
    c2 = encrypt_string(seed, "value")
    assert c1 != c2


def test_decrypt_with_wrong_seed_returns_none():
    seed1 = _make_seed()
    seed2 = _make_seed()
    ciphertext = encrypt_string(seed1, "secret")
    result = decrypt_string(seed2, ciphertext)
    assert result is None


def test_encrypt_empty_string():
    seed = _make_seed()
    ciphertext = encrypt_string(seed, "")
    assert decrypt_string(seed, ciphertext) == ""
