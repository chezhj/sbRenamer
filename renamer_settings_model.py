""" Model for the renaming engine
    Includes settings that are saved in ini file via configparser
    settings are defined as properties
    Logging to file and normal logging is also configured in this model
 """
import logging
import configparser
import pathlib
import errno
import os
import re

from listener_logger_handler import LoggerHandler


class RenamerSettings:
    """Actual model for settings"""

    SHORT_FORMAT = "ICAOICOA.xml"
    ZERO_FORMAT = "ICAOICOA01.xml"
    # Mod 15
    B738_FORMAT = "b738x.xml"
    LOGLEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
    FILEFORMATS = [B738_FORMAT, SHORT_FORMAT, ZERO_FORMAT]
    LOGFILENAME = "log.txt"
    FMS_NO = "NO"
    FMS_B738 = "b738x"
    FMS_BOTH = "BOTH"
    FMS_OPTIONS = [FMS_NO, FMS_B738, FMS_BOTH]

    WIDGIT_LOG_FORMAT = {
        "fmt": "%(asctime)s - %(levelname)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }
    FILE_LOG_FORMAT = {
        "fmt": "%(asctime)s - %(levelname)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }

    def __init__(self, cnf_file_name):
        self._config = configparser.ConfigParser()
        self._dirty = True

        if not self._config.read(cnf_file_name):
            logging.error("No configfile (%s) found", cnf_file_name)
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), cnf_file_name
            )
        self._dirty = False
        self._monitoring = False
        self._call_back = None
        self._log_file_handler = None
        self._log_listener = None

        self._ini_file_name = cnf_file_name
        self._log_handler = LoggerHandler(logging.INFO, self.WIDGIT_LOG_FORMAT)
        self._add_loghandler_to_logger()
        self._set_file_logging()

        # Base loghandler is always lowest level
        logging.getLogger().setLevel(logging.DEBUG)
        # Widget handler should always be on INFO
        self._log_handler.setLevel(logging.INFO)
        logging.info("Configuration loaded from: %s", cnf_file_name)

    def __set_value(self, key, value):
        if value == self._config["BaseSettings"].get(key):
            logging.debug(
                "New value %s is the same as current %s",
                value,
                self._config["BaseSettings"].get(key),
            )
            return False
        self._config["BaseSettings"][key] = value
        self._dirty = True
        if self._call_back:
            self._call_back()

        logging.debug("SetValue: %s set to: %s", key, value)
        return True

    @property
    def dirty(self):
        """Indicates if a setting has changed but not saved yet"""
        return self._dirty

    @property
    def monitoring(self):
        """Used to register if the file listener is active"""
        return self._monitoring

    @monitoring.setter
    def monitoring(self, value):
        self._monitoring = value

    @property
    def source_dir(self):
        """Directory/path that is used to monitor"""
        return pathlib.Path(self._config["BaseSettings"].get("source_dir", "."))

    @source_dir.setter
    def source_dir(self, value):
        self.__set_value("source_dir", value)

    @property
    def file_format(self):
        """Setting wich format should be used"""
        return self._config["BaseSettings"].get("file_format", self.SHORT_FORMAT)

    @file_format.setter
    def file_format(self, value):
        if self.__set_value("file_format", value):
            logging.info("Changed filename format to %s", self.file_format)

    @property
    def auto_start(self):
        """setting to make sbRenamer start automaticly"""
        return self._config["BaseSettings"].getboolean("auto_start", False)

    @auto_start.setter
    def auto_start(self, value: bool):
        if self.__set_value("auto_start", str(value)):
            logging.info("Changed autostart to %s", self.auto_start)

    @property
    def auto_hide(self):
        """settig to make sbRenamer hide in the windows system tray"""
        return self._config["BaseSettings"].getboolean("auto_hide", False)

    @auto_hide.setter
    def auto_hide(self, value: bool):
        if self.__set_value("auto_hide", str(value)):
            logging.info("Changed auto_hide to %s", self.auto_hide)

    @property
    def save_xml(self):
        """property to indicate if you want to copy (safe) or rename"""
        return self._config["BaseSettings"].getboolean("save_XML", True)

    @save_xml.setter
    def save_xml(self, value: bool):
        if self.__set_value("save_XML", str(value)):
            logging.info("Changed save_XML to %s", self.save_xml)

    @property
    def number_of_days(self):
        """Number of days that a file must be aged before it will be deleted. 0 means no delete"""
        return self._config["BaseSettings"].get("number_of_days", "0")

    @number_of_days.setter
    def number_of_days(self, value):
        if not value:
            self.__set_value("number_of_days", "0")
        elif self.validate_number(value):
            self.__set_value("number_of_days", value)
        else:
            raise TypeError("Number of days should be a number")

    @property
    def fms_format(self):
        """Setting wich format should be used"""
        return self._config["BaseSettings"].get("fms_format", self.FMS_BOTH)

    @fms_format.setter
    def fms_format(self, value):
        if self.__set_value("fms_format", value):
            logging.info("Changed filename format to %s", self.fms_format)

    @property
    def log_level(self):
        """property to set log level, DEBUG,INFO, WARINING,"""
        return self._config["BaseSettings"].get("loglevel", "ERROR")

    @log_level.setter
    def log_level(self, value):
        if self.__set_value("loglevel", value):
            if self._log_file_handler:
                self._log_file_handler.setLevel(self.log_level)

            # Base loghandler is always lowest level
            logging.getLogger().setLevel(logging.DEBUG)
            # Widget handler should always be on INFO
            self._log_handler.setLevel(logging.INFO)
            logging.info("Altered log level to %s", self.log_level)

    @property
    def log_to_file(self):
        """Set to true if you want a file"""
        return self._config["BaseSettings"].getboolean("log_to_file", False)

    @log_to_file.setter
    def log_to_file(self, value: bool):
        if self.__set_value("log_to_file", str(value)):
            self._set_file_logging()

    def set_callback(self, callback):
        """setter for callback propery, callback will be called on save"""
        self._call_back = callback

    def remove_callback(self):
        """sets callback property to None"""
        self._call_back = None

    def set_log_listener(self, log_listener):
        """
        Setter for internal propery log listener
        Listener will be called every time line is logged
        """
        self._log_listener = log_listener
        self._log_handler.set_listener(log_listener)

    def remove_log_listener(self):
        """set log listener to none"""
        self._log_listener = None

    def _add_loghandler_to_logger(self):
        """Adds internal handler to default logger"""
        logger = logging.getLogger()
        logger.addHandler(self._log_handler)
        logging.info("Added custom log handler for logging")

    def _set_file_logging(self):
        """Add file logger to default logger"""
        logger = logging.getLogger()

        if self.log_to_file == 1:
            # check if there is a file handler

            file = pathlib.Path(self.LOGFILENAME).resolve()

            if file.exists():
                file.unlink()

            if not self._log_file_handler:
                self._log_file_handler = logging.FileHandler(self.LOGFILENAME)
                self._log_file_handler.setFormatter(
                    logging.Formatter(**self.FILE_LOG_FORMAT)
                )
                self._log_file_handler.setLevel(self.log_level)
                logger.addHandler(self._log_file_handler)

                logging.info("Added file handler for logging to %s", self.LOGFILENAME)
        else:
            if self._log_file_handler:
                logger.removeHandler(self._log_file_handler)
                self._log_file_handler.flush()
                self._log_file_handler.close()
                self._log_file_handler = None
                logging.info("Removed file handler for logging")

    def save(self):
        """Save settings to config file"""
        with open(self._ini_file_name, mode="w", encoding="utf-8") as configfile:
            self._config.write(configfile)
            logging.info("Saved configurarion")
            self._dirty = False
            if self._call_back:
                self._call_back()

    # debatable if this is really af method of this class
    def new_filename(self, current_filename):
        """returns target filename based on format"""
        if self.file_format == self.SHORT_FORMAT:
            return pathlib.Path(current_filename[:8] + ".xml")
        if self.file_format == self.ZERO_FORMAT:
            return pathlib.Path(current_filename[:8] + "01.xml")

        # Mod 15
        if self.file_format == self.B738_FORMAT:
            return pathlib.Path("b738x.xml")

    def fms_filename(self):
        """function that returs the fms filename"""
        return pathlib.Path("b738x.fms")

    def validate_number(self, value):
        """function to validate if a string contains a positive number"""
        return bool(re.search(r"\d", value))
