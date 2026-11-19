"""Test JWKS cache duration"""

import pytest

def test_jwks_cache_duration():
    with open("backend/app/services/auth.py") as f:
        content = f.read()
        assert "total_seconds() < 300" in content
