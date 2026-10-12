"""Tests for the initial HashScrap command-line interface."""

from __future__ import annotations

import pytest

from hashscrap import __version__
from hashscrap.cli import main


def test_cli_without_arguments_displays_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "HashScrap" in output
    assert "--version" in output


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert f"hashscrap {__version__}" in capsys.readouterr().out


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    assert "usage:" in capsys.readouterr().out.lower()
