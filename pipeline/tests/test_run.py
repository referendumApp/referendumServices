import pytest
import subprocess
import os


def is_running_in_docker():
    return os.path.exists("/.dockerenv")


def test_pipeline_execution():
    if not is_running_in_docker():
        pytest.skip("This test should only run inside a Docker container")

    result = subprocess.run(["python", "-m", "pipeline.run"], capture_output=True, text=True, check=True)
    full_output = result.stdout + result.stderr
    assert "ETL process completed successfully" in full_output, "Success message not found in pipeline output"
