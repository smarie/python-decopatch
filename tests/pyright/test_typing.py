import sys

import pytest

from .base import run_pyright, pyright_installed


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="Requires Python 3.7+",
)
@pytest.mark.skipif(
    not pyright_installed,
    reason="Pyright not installed",
)
def test_typing(snapshot):
    """Test that pyright detects the typing issues on `test_file` correctly."""
    actual = run_pyright("tests/pyright/test_file.py")
    assert actual == snapshot
