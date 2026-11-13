"""Execute the original C core's state/fault/protocol regression suite."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_generated_parameters_are_current():
    subprocess.run([sys.executable, ROOT / "tools/generate_config.py", "--check"], check=True)


def test_native_control_regressions():
    binary = ROOT / "firmware/build" / ("control_tests.exe" if os.name == "nt" else "control_tests")
    if not binary.exists():
        subprocess.run([sys.executable, ROOT / "firmware/build.py", "--target", "host"], check=True)
    result = subprocess.run([binary], check=True, capture_output=True, text=True, timeout=10)
    assert "PASS " in result.stdout
    assert "assertions" in result.stdout
