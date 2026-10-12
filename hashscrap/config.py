"""Validated source registry and collection limits.

These models intentionally do not depend on Scrapy or a persistence backend.
"""
from __future__ import annotations

import os
import tomllib
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, ValidationError, model_validator


class ConfigurationError(ValueError):
    """Raised when the configuration file cannot be loaded safely."""


class SourceKind(StrEnum):
    """Supported source categories for the initial registry."""

    WEBSITE = "website"
    API = "api"
    FEED = "feed"
    DATASET = "dataset"


class CollectionLimits(BaseModel):
    """Per-source limits. All values are bounded to conservative ranges."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    timeout_seconds: int = Field(default=15, ge=1, le=120)
    max_pages: int = Field(default=100, ge=1, le=10_000)
    max_depth: int = Field(default=2, ge=0, le=10)
    concurrency: int = Field(default=4, ge=1, le=16)
    requests_per_second: float = Field(default=1.0, gt=0, le=10)
    max_response_bytes: int = Field(default=2_000_000, ge=1_024, le=10_000_000)
    max_retries: int = Field(default=2, ge=0, le=5)


class RegistryLimits(BaseModel):
    """Global ceilings that no source-specific policy may exceed."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_pages_per_source: int = Field(default=1_000, ge=1, le=10_000)
    max_depth: int = Field(default=5, ge=0, le=10)
    max_concurrency: int = Field(default=16, ge=1, le=32)
    max_response_bytes: int = Field(default=5_000_000, ge=1_024, le=10_000_000)


class SourceDefinition(BaseModel):
    """A named source with an explicit enablement state and collection policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=2, max_length=63, pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: str = Field(min_length=1, max_length=120)
    kind: SourceKind
    base_url: AnyHttpUrl
    enabled: bool = True
    limits: CollectionLimits = Field(default_factory=CollectionLimits)


class SourceRegistry(BaseModel):
    """Validated collection configuration and source selection helpers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    limits: RegistryLimits = Field(default_factory=RegistryLimits)
    sources: tuple[SourceDefinition, ...] = ()

    @model_validator(mode="after")
    def validate_sources(self) -> SourceRegistry:
        source_ids = [source.id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source IDs must be unique")

        for source in self.sources:
            if source.limits.max_pages > self.limits.max_pages_per_source:
                raise ValueError("source max_pages exceeds the global limit")
            if source.limits.max_depth > self.limits.max_depth:
                raise ValueError("source max_depth exceeds the global limit")
            if source.limits.concurrency > self.limits.max_concurrency:
                raise ValueError("source concurrency exceeds the global limit")
            if source.limits.max_response_bytes > self.limits.max_response_bytes:
                raise ValueError("source response size exceeds the global limit")

        return self

    def get_enabled_source(self, source_id: str) -> SourceDefinition | None:
        """Return a source only when it exists and is enabled."""
        for source in self.sources:
            if source.id == source_id and source.enabled:
                return source
        return None


def load_registry(path: str | Path | None = None) -> SourceRegistry:
    """Load and validate a TOML registry without echoing invalid input values."""
    config_path = Path(path) if path is not None else Path(
        os.environ.get("HASHSCRAP_CONFIG", "hashscrap.toml")
    )

    try:
        with config_path.open("rb") as config_file:
            payload: dict[str, Any] = tomllib.load(config_file)
    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {config_path}") from None
    except tomllib.TOMLDecodeError:
        raise ConfigurationError("Configuration file is not valid TOML.") from None
    except OSError:
        raise ConfigurationError("Configuration file could not be read.") from None

    try:
        return SourceRegistry.model_validate(payload)
    except ValidationError:
        raise ConfigurationError(
            "Configuration values are invalid; check source fields and configured limits."
        ) from None
