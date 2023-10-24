"""Unit tests for RenamerSettings Module"""
import unittest
from unittest.mock import ANY, Mock, mock_open, patch

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

    def test_monitoring_setter_true(self):
        rsm = RenamerSettings("test/empty_config.ini")
        rsm.monitoring = True
        self.assertTrue(rsm.monitoring)

    @patch("renamer_settings_model.configparser.ConfigParser.get")
    @patch("renamer_settings_model.open", create=True)
    @patch("renamer_settings_model.configparser.ConfigParser.write")
    def test_config_writer(self, mock_write, mock_file_open, mock_get):
        mock_key_values = {
            "log_to_file": "True",
            "auto_start": "False",
            "loglevel": "ERROR",
        }

        mock_get.side_effect = lambda section, key, **kwargs: mock_key_values.get(
            key, ""
        )
        handle_mock = Mock()
        mock_file_open.return_value.__enter__.return_value = handle_mock

        rsm = RenamerSettings("test/empty_config.ini")

        self.assertTrue(rsm.log_to_file)
        rsm.source_dir = r"c:\ddd"
        rsm.save()
        mock_file_open.assert_called_once_with(
            "test/empty_config.ini", mode="w", encoding="utf-8"
        )
        self.assertFalse(rsm.dirty)
        mock_write.assert_called_once_with(handle_mock)

    @patch("renamer_settings_model.configparser.ConfigParser.get")
    @patch("renamer_settings_model.configparser.ConfigParser.write")
    @unittest.skip
    def test_config_writer_two(self, mock_write, mock_get):
        mock_key_values = {
            "log_to_file": "True",
            "auto_start": "False",
            "loglevel": "ERROR",
        }

        mock_get.side_effect = lambda section, key, **kwargs: mock_key_values.get(
            key, ""
        )

        # Create a custom context manager for open using lambda
        custom_open = lambda name, mode, encoding: mock_open()()

        # Create a mock file handle
        mock_file_handle = mock_open()()

        with patch("renamer_settings_model.open", custom_open) as mock_patch_open:
            rsm = RenamerSettings("test/empty_config.ini")
            self.assertTrue(rsm.log_to_file)
            rsm.source_dir = r"c:\ddd"
            rsm.save()
            mock_patch_open.assert_called_once_with(
                "test/empty_config.ini", mode="w", encoding="utf-8"
            )
            self.assertFalse(rsm.dirty)
            mock_write.assert_called_once_with(mock_file_handle)
