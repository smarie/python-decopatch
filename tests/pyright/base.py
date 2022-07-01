import json
import shutil
import subprocess

__all__ = ["run_pyright", "pyright_installed"]

try:
    pyright_bin = shutil.which("pyright")
    pyright_installed = pyright_bin is not None
except AttributeError:
    # shutil.which works from python 3.3 onward
    pyright_bin = None
    pyright_installed = False


def run_pyright(filename):
    """
    Executes pyright type checker against a file, and returns json output.

    Used together with syrupy snapshot to check if typing is working as expected.
    """
    result = subprocess.run(
        [pyright_bin, "--outputjson", filename],
        capture_output=True,
        text=True,
    )
    assert result.stdout, result.stderr
    output = json.loads(result.stdout)

    def format_row(data):
        # Remove "file" from json report, it has no use here.
        del data["file"]
        return data

    return [format_row(row) for row in output["generalDiagnostics"]]
