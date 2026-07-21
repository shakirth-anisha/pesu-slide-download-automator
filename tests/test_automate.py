import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automate import sanitize, login, select_course, select_semester


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


class FakeOption:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def text_content(self):
        return self.name

    def inner_text(self):
        # Playwright returns "" here for options in a closed select.
        return ""

    def get_attribute(self, attribute):
        assert attribute == "value"
        return self.value


class FakeList:
    def __init__(self, items):
        self.items = items

    def count(self):
        return len(self.items)

    def nth(self, index):
        return self.items[index]

    @property
    def first(self):
        return self.items[0]


class FakeRow:
    def __init__(self, text):
        self.text = text

    def inner_text(self):
        return self.text


class FakeSelect:
    def __init__(self, value):
        self.value = value

    def input_value(self):
        return self.value


class FakeSemesterPage:
    """Minimal stand-in for the My Courses page and its AJAX refresh."""

    def __init__(self, current_value, semesters):
        self.current_value = current_value
        self.semesters = semesters
        self.selected = None
        self.rows = ["CS101 Course A"]
        self.waits = []

    def wait_for_selector(self, selector, **kwargs):
        self.waits.append((selector, kwargs.get("state")))

    def wait_for_timeout(self, *args, **kwargs):
        # The course table only swaps in once a new semester is chosen.
        if self.selected is not None:
            self.rows = ["CS201 Course B"]

    def select_option(self, selector, value=None):
        assert selector == "#semesters"
        self.selected = value

    def locator(self, selector):
        if selector == "#semesters option":
            return FakeList(
                [FakeOption(name, value) for name, value in self.semesters]
            )
        if selector == "#semesters":
            return FakeSelect(self.current_value)
        if selector == "table.table.table-hover tbody tr":
            return FakeList([FakeRow(text) for text in self.rows])
        raise AssertionError(f"Unexpected selector: {selector}")


def test_select_semester_uses_semester_number_not_list_position():
    """The site lists newest first, so entering 3 must mean Sem-3, which is
    last in the dropdown, not the third entry."""
    page = FakeSemesterPage(
        "3247",
        [("Sem-8", "3247"), ("Sem-7", "2967"), ("Sem-3", "1987")],
    )

    with patch("builtins.input", return_value="3"):
        name = select_semester(page)

    assert name == "Sem-3"
    assert page.selected == "1987"


def test_select_semester_current_semester_skips_reselect():
    page = FakeSemesterPage("3247", [("Sem-8", "3247"), ("Sem-7", "2967")])

    with patch("builtins.input", return_value="8"):
        name = select_semester(page)

    assert name == "Sem-8"
    assert page.selected is None


def test_select_semester_reprompts_on_invalid_input():
    page = FakeSemesterPage("3247", [("Sem-8", "3247"), ("Sem-7", "2967")])

    with patch("builtins.input", side_effect=["", "2", "abc", "7"]):
        name = select_semester(page)

    assert name == "Sem-7"
    assert page.selected == "2967"


def test_select_semester_waits_for_options_as_attached():
    """A closed <select> never renders its options, so waiting on the
    default visible state times out."""
    page = FakeSemesterPage("3247", [("Sem-8", "3247"), ("Sem-7", "2967")])

    with patch("builtins.input", return_value="8"):
        select_semester(page)

    assert ("#semesters option", "attached") in page.waits


def test_select_course_returns_none_when_semester_empty():
    mock_page = MagicMock()
    no_content = MagicMock()
    no_content.is_visible.return_value = True
    rows = MagicMock()
    rows.count.return_value = 0

    def locator(selector):
        if selector == "h2:text('No subjects found')":
            return no_content
        return rows

    mock_page.locator.side_effect = locator

    assert select_course(mock_page) is None
