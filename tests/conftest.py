import tempfile
import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_path:
        yield temp_path
