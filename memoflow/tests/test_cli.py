"""Tests for CLI module"""

import pytest
from mf.cli import app


def test_cli_app_exists():
    """Test that CLI app is properly initialized"""
    assert app is not None
    assert hasattr(app, "command")


def test_version_function_exists():
    """Test that version function can be imported"""
    from mf import __version__
    assert __version__ == "0.1.0"
