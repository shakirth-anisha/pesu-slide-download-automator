import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automate import sanitize, login


def test_sanitize_basic():
    assert sanitize("My-Course Name!") == "My-Course Name"


def test_login_success():
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_locator.is_visible.return_value = False
    mock_page.locator.return_value = mock_locator

    result = login(mock_page, "user123", "pass456")

    assert result is True


def test_login_failure_user_not_found():
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_locator.is_visible.return_value = True
    mock_locator.inner_text.return_value = "User doesn't exist"
    mock_page.locator.return_value = mock_locator

    with pytest.raises(ValueError):
        login(mock_page, "invalid_user", "pass456")
