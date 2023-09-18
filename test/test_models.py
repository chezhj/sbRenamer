"""Unit tests for RenamerSettings Module"""
import unittest


# pylint: disable=missing-function-docstring
## from unittest.mock import MagicMock, patch

from renamer_settings_model import RenamerSettings


class TestRenamerSettings(unittest.TestCase):
    """main test class for all properties"""

    def test_default_autostart_false(self):
        rsm = RenamerSettings("test/empty_config.ini")
        self.assertFalse(rsm.auto_start)

    def test_default_autohide_false(self):
        rsm = RenamerSettings("test/empty_config.ini")
        self.assertFalse(rsm.auto_hide)

    def test_non_existing_file(self):
        with self.assertRaises(FileNotFoundError):
            RenamerSettings("test/non_existing.ini")

    def test_dirty_should_be_false_after_init(self):
        rsm = RenamerSettings("test/empty_config.ini")
        self.assertFalse(rsm.dirty)

    def test_monitoring_should_be_false_after_init(self):
        rsm = RenamerSettings("test/empty_config.ini")
        self.assertFalse(rsm.monitoring)

    def test_return_source_dir(self):
        rsm = RenamerSettings("test/empty_config.ini")
        self.assertEqual(str(rsm.source_dir), r"N:\dir\source_dir")
