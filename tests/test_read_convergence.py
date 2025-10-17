"""
Test for the read_convergence method to ensure it handles edge cases properly.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from xespresso.xespresso import Espresso


def create_mock_calculator(tmpdir, label="test"):
    """Create a mock Espresso calculator for testing read_convergence"""
    calc = Mock(spec=Espresso)
    calc.label = os.path.join(tmpdir, label)
    # Bind the actual read_convergence method to the mock
    calc.read_convergence = Espresso.read_convergence.__get__(calc, Espresso)
    return calc


def test_read_convergence_empty_file():
    """Test that read_convergence handles empty .pwo files correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an empty .pwo file
        pwo_file = os.path.join(tmpdir, "test.pwo")
        with open(pwo_file, 'w') as f:
            f.write("")
        
        # Create a mock Espresso calculator
        calc = create_mock_calculator(tmpdir)
        
        # Test read_convergence with empty file
        convergence, message = calc.read_convergence()
        assert convergence == 1
        assert "pwo file has nothing" in message


def test_read_convergence_single_line_file():
    """Test that read_convergence handles .pwo files with only one line"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a .pwo file with only one line
        pwo_file = os.path.join(tmpdir, "test.pwo")
        with open(pwo_file, 'w') as f:
            f.write("Single line content\n")
        
        # Create a mock Espresso calculator
        calc = create_mock_calculator(tmpdir)
        
        # Test read_convergence with single line file
        # Should not crash with IndexError
        convergence, message = calc.read_convergence()
        # Should return 4 (unknown error) since no recognized patterns found
        assert convergence == 4


def test_read_convergence_job_done():
    """Test that read_convergence correctly identifies successful completion"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a .pwo file with JOB DONE message
        pwo_file = os.path.join(tmpdir, "test.pwo")
        with open(pwo_file, 'w') as f:
            f.write("Program PWSCF starts on 17Oct2025 at 12:00:00\n")
            f.write("Some calculation output\n")
            for _ in range(10):
                f.write("More output lines\n")
            f.write("     JOB DONE.\n")
            f.write("\n")
        
        # Create a mock Espresso calculator
        calc = create_mock_calculator(tmpdir)
        
        # Test read_convergence with successful job
        convergence, message = calc.read_convergence()
        assert convergence == 0
        assert "JOB DONE" in message


def test_read_convergence_not_converged():
    """Test that read_convergence correctly identifies non-convergence"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a .pwo file with convergence NOT achieved message
        pwo_file = os.path.join(tmpdir, "test.pwo")
        with open(pwo_file, 'w') as f:
            f.write("Program PWSCF starts on 17Oct2025 at 12:00:00\n")
            f.write("Some calculation output\n")
            for _ in range(10):
                f.write("More output lines\n")
            f.write("     convergence NOT achieved after 100 iterations: stopping\n")
            f.write("\n")
        
        # Create a mock Espresso calculator
        calc = create_mock_calculator(tmpdir)
        
        # Test read_convergence with non-converged job
        convergence, message = calc.read_convergence()
        assert convergence == 1
        assert "convergence NOT achieved" in message


def test_read_convergence_missing_file():
    """Test that read_convergence handles missing .pwo files correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Don't create a .pwo file
        
        # Create a mock Espresso calculator
        calc = create_mock_calculator(tmpdir)
        
        # Test read_convergence with missing file
        convergence, message = calc.read_convergence()
        assert convergence == 3
        assert "No pwo output file" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
