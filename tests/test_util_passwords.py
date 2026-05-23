"""
Tests for genericsuite/util/passwords.py — Passwords class.
"""
import sys
import types

# Remove any cached mocked version of passwords so we get the real one
for _mod in list(sys.modules):
    if "genericsuite.util.passwords" in _mod:
        del sys.modules[_mod]

# Force our Config stub (override any previous mock)
_cfg_mod = types.ModuleType("genericsuite.config.config")


class _StubConfig:
    APP_SECRET_KEY = "test_secret_key"


_cfg_mod.Config = _StubConfig
sys.modules["genericsuite.config.config"] = _cfg_mod

from genericsuite.util.passwords import Passwords


def test_hash_and_verify_correct_password():
    p = Passwords()
    hashed = p.encrypt_password("mypassword")
    assert p.verify_password(hashed, "mypassword") is True


def test_verify_wrong_password_fails():
    p = Passwords()
    hashed = p.encrypt_password("correctpass")
    assert p.verify_password(hashed, "wrongpass") is False


def test_hash_does_not_contain_plaintext():
    p = Passwords()
    password = "supersecret123"
    hashed = p.encrypt_password(password)
    assert password not in hashed


def test_two_hashes_of_same_password_differ():
    """scrypt hashes include random salt, so hashes must differ."""
    p = Passwords()
    h1 = p.encrypt_password("same")
    h2 = p.encrypt_password("same")
    assert h1 != h2


def test_passwords_encryption_updates_fields():
    p = Passwords()
    data = {"password": "plain", "other": "value"}
    result = p.passwords_encryption(data, ["password"])
    assert result["password"] != "plain"
    assert result["other"] == "value"
