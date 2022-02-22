import pytest
import sys
from .base import run_pyright


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="Requires Python 3.7+",
)
def test_typing(snapshot):
    actual = run_pyright("tests/pyright/test_file.py")
    assert actual == snapshot
