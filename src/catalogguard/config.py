"""Environment-driven settings."""

from __future__ import annotations

import os
from collections.abc import Mapping

from pydantic import BaseModel

_FALSEY = {"false", "0", "no", "off"}


class Settings(BaseModel):
    """Runtime configuration resolved from the environment."""

    magento_base_url: str
    magento_access_token: str = ""
    magento_verify_ssl: bool = True
    llm_provider: str = "claude"
    llm_model: str = "claude-opus-4-8"
    anthropic_api_key: str = ""


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Build Settings from a mapping (defaults to ``os.environ``).

    Raises ``KeyError`` if the required Magento base URL is absent — fail loud
    rather than audit the wrong store.
    """
    env = os.environ if env is None else env
    return Settings(
        magento_base_url=env["MAGENTO_BASE_URL"],
        magento_access_token=env.get("MAGENTO_ACCESS_TOKEN", ""),
        magento_verify_ssl=env.get("MAGENTO_VERIFY_SSL", "true").lower() not in _FALSEY,
        llm_provider=env.get("CATALOGGUARD_LLM_PROVIDER", "claude"),
        llm_model=env.get("CATALOGGUARD_LLM_MODEL", "claude-opus-4-8"),
        anthropic_api_key=env.get("ANTHROPIC_API_KEY", ""),
    )
