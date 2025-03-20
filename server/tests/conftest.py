"""
pytest configuration file for the server tests.
This file sets up fixtures and configuration for all test files.
"""

import pytest
import os
import sys

# Ensure the server directory is in the Python path
server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)
