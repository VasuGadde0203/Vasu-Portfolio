"""Vercel installs from pyproject.toml, Docker from requirements.txt: they must list the same packages."""

import tomllib
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def test_pyproject_and_requirements_list_the_same_dependencies():
    declared = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]
    required = [
        line.strip() for line in (BACKEND / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert sorted(declared) == sorted(required)
