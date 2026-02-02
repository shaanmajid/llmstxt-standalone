"""Example tests for the llmstxt_standalone package."""

import re

from llmstxt_standalone import __version__


def test_version() -> None:
    """Test that version is defined and follows semver format."""
    assert re.match(r"^\d+\.\d+\.\d+", __version__)
