"""This module is only to be used together with tests
"""
import os
import subprocess
import pytest


def set_envs():
    """Detect pw"""
    import os

    cwd = os.getcwd()
    os.environ["ESPRESSO_PSEUDO"] = os.path.join(cwd, "datas/pseudo")
    os.environ[
        "ASE_ESPRESSO_COMMAND"
    ] = "PACKAGE.x PARALLEL -in PREFIX.PACKAGEi > PREFIX.PACKAGEo"


def espresso_available():
    """Check if Quantum ESPRESSO executables are available"""
    try:
        # Check if pw.x is available
        result = subprocess.run(['which', 'pw.x'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False


# Pytest fixtures and decorators
skip_if_no_espresso = pytest.mark.skipif(
    not espresso_available(),
    reason="Quantum ESPRESSO not available"
)
