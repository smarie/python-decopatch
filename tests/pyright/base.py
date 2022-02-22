import json
import subprocess


def run_pyright(filename):
    result = subprocess.run(
        ["pyright", "--outputjson", filename],
        capture_output=True,
        text=True,
    )
    assert result.stdout, result.stderr
    output = json.loads(result.stdout)

    def clean_row(data):
        del data["file"]
        return data

    return [clean_row(row) for row in output["generalDiagnostics"]]
