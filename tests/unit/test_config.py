"""Tests for environment-driven settings loading."""

from __future__ import annotations

import pytest

from catalogguard.config import Settings, load_settings


def test_load_settings_reads_required_and_optional_fields() -> None:
    settings = load_settings(
        {
            "MAGENTO_BASE_URL": "https://app.demo.test",
            "MAGENTO_ACCESS_TOKEN": "tok123",
            "MAGENTO_VERIFY_SSL": "false",
        }
    )
    assert isinstance(settings, Settings)
    assert settings.magento_base_url == "https://app.demo.test"
    assert settings.magento_access_token == "tok123"
    assert settings.magento_verify_ssl is False


def test_load_settings_defaults_verify_ssl_true_when_absent() -> None:
    settings = load_settings({"MAGENTO_BASE_URL": "https://x"})
    assert settings.magento_verify_ssl is True
    assert settings.magento_access_token == ""


def test_load_settings_requires_base_url() -> None:
    with pytest.raises(KeyError):
        load_settings({})
