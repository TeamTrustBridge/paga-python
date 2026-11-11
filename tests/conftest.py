"""Shared pytest fixtures for the paga-python test suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

# The hash vectors live inside this repository so the package is
# self-contained. The copy at the monorepo root is the canonical one shared
# with the TypeScript and Rust SDKs; it is preferred when present so the
# three stay in step.
REPO_ROOT = Path(__file__).resolve().parents[2]
MONOREPO_FIXTURE = REPO_ROOT / "fixtures" / "hash_vectors.json"
LOCAL_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "hash_vectors.json"
HASH_VECTORS_PATH = (
    MONOREPO_FIXTURE if MONOREPO_FIXTURE.exists() else LOCAL_FIXTURE
)


def _load_vectors() -> Dict[str, Any]:
    if not HASH_VECTORS_PATH.exists():  # pragma: no cover - layout guard
        pytest.skip(f"shared hash vectors not found at {HASH_VECTORS_PATH}")
    with HASH_VECTORS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="session")
def hash_vectors() -> Dict[str, Any]:
    """The shared cross-SDK hash vector fixture."""
    return _load_vectors()


@pytest.fixture(scope="session")
def hash_key(hash_vectors: Dict[str, Any]) -> str:
    """The hash key used by the shared vectors."""
    return hash_vectors["hashKey"]
