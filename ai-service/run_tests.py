#!/usr/bin/env python3
"""
Test runner script for the AI Service.
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run the test suite."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent

    # Change to the script directory
    import os

    os.chdir(script_dir)

    # Run pytest
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]

    print("Running tests...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
