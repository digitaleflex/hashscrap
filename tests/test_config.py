"""Tests for source registry validation and configuration loading."""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from hashscrap.config import ConfigurationError, SourceRegistry, load_registry


def valid_payload() -> dict[str, object]:
    return {
        "limits": {
            "max_pages_per_source": 100,
            "max_depth": 3,
            "max_concurrency": 8,
            "max_response_bytes": 2_000_000,
        },
        "sources": [
            {
                "id": "public-site",
                "name": "Public site",
                "kind": "website",
                "base_url": "https://example.org",
                "enabled": True,
                "limits": {
                    "max_pages": 50,
                    "max_depth": 2,
                    "concurrency": 4,
                    "max_response_bytes": 1_000_000,
                },
            }
        ],
    }


def test_valid_registry_is_normalized() -> None:
    registry = SourceRegistry.model_validate(valid_payload())

    assert registry.get_enabled_source("public-site") is not None
    assert registry.get_enabled_source("missing") is None
    assert registry.sources[0].limits.max_pages == 50


def test_disabled_source_cannot_be_selected() -> None:
    payload = valid_payload()
    sources = payload["sources"]
    assert isinstance(sources, list)
    source = sources[0]
    assert isinstance(source, dict)
    source["enabled"] = False

    registry = SourceRegistry.model_validate(payload)

    assert registry.get_enabled_source("public-site") is None


def test_duplicate_source_ids_are_rejected() -> None:
    payload = valid_payload()
    sources = payload["sources"]
    assert isinstance(sources, list)
    sources.append(dict(sources[0]))

    with pytest.raises(ValidationError, match="source IDs must be unique"):
        SourceRegistry.model_validate(payload)


def test_source_cannot_exceed_global_page_limit() -> None:
    payload = valid_payload()
    sources = payload["sources"]
    assert isinstance(sources, list)
    source = sources[0]
    assert isinstance(source, dict)
    limits = source["limits"]
    assert isinstance(limits, dict)
    limits["max_pages"] = 101

    with pytest.raises(ValidationError, match="exceeds the global limit"):
        SourceRegistry.model_validate(payload)


def test_invalid_limits_are_rejected() -> None:
    payload = valid_payload()
    sources = payload["sources"]
    assert isinstance(sources, list)
    source = sources[0]
    assert isinstance(source, dict)
    limits = source["limits"]
    assert isinstance(limits, dict)
    limits["concurrency"] = 0

    with pytest.raises(ValidationError):
        SourceRegistry.model_validate(payload)


def test_load_registry_from_toml(tmp_path: Path) -> None:
    config_path = tmp_path / "hashscrap.toml"
    config_path.write_text(
        '[limits]\nmax_pages_per_source = 100\nmax_depth = 3\n'
        'max_concurrency = 8\nmax_response_bytes = 2000000\n\n'
        '[[sources]]\nid = "public-site"\nname = "Public site"\n'
        'kind = "website"\nbase_url = "https://example.org"\nenabled = true\n',
        encoding="utf-8",
    )

    registry = load_registry(config_path)

    assert registry.get_enabled_source("public-site") is not None


def test_invalid_toml_has_safe_error(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.toml"
    config_path.write_text("not = [valid", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="not valid TOML"):
        load_registry(config_path)


def test_missing_config_has_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_registry(tmp_path / "missing.toml")
