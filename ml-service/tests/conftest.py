"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Ensure app modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
