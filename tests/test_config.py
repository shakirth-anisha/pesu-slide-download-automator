import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config


def test_get_username_default():
    with pytest.MonkeyPatch().context() as m:
        m.delenv('USERNAME', raising=False)
        assert Config.get_username() == ''


def test_set_merge_pdfs_preference_invalid():
    with pytest.raises(ValueError):
        Config.set_merge_pdfs_preference('invalid')


def test_is_debug_enabled_true():
    with pytest.MonkeyPatch().context() as m:
        m.setenv('DEBUG', '1')
        assert Config.is_debug_enabled() is True
    
