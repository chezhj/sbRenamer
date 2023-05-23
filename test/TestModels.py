import unittest

from unittest.mock import MagicMock, patch

from RenamerSettingsModel import RenamerSettings


class TestRenamerSettings(unittest.TestCase):
    def test_default_autostart_false(self):
        rsm = RenamerSettings("test/empty_config.ini")
        self.assertFalse(rsm.autoStart)

    def test_default_autohide_false(self):
        rsm = RenamerSettings("test/empty_config.ini")
        self.assertFalse(rsm.autoHide)
