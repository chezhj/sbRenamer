import logging
import configparser
import pathlib
import errno
import os


class RenamerSettings:

    SHORT_FORMAT = "ICAOICOA.xml"
    ZERO_FORMAT = "ICAOICOA01.xml"
    LOGLEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
    FILEFORMATS = [SHORT_FORMAT, ZERO_FORMAT]
    LOGFILENAME = "log.txt"

    WIDGIT_LOG_FORMAT = {
        "fmt": "%(asctime)s - %(levelname)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }
    FILE_LOG_FORMAT = {
        "fmt": "%(asctime)s - %(levelname)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }

    def __init__(self, cnfFileName):
        self._config = configparser.ConfigParser()
        self._dirty = True
        if self._config.read(cnfFileName) == []:
            logging.error("No configfile (%s) found" % cnfFileName)
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), cnfFileName
            )
        self._dirty = False
        self._monitoring = False
        self._callBack = None
        self._logFileHandler = None
        self._iniFileName = cnfFileName
        self._logHandler = loggerHandler(logging.INFO, self.WIDGIT_LOG_FORMAT)
        self._addLogHandlerToLogger()
        self._setFileLogging()

        # Base loghandler is always lowest level
        logging.getLogger().setLevel(logging.DEBUG)
        # Widget handler should always be on INFO
        self._logHandler.setLevel(logging.INFO)
        logging.info("Configuration loaded from: %s" % cnfFileName)

    def __setValue(self, key, value):
        if value == self._config["BaseSettings"].get(key):
            logging.debug(
                "New value %s is the same as current %s",
                value,
                self._config["BaseSettings"].get(key),
            )
            return False
        self._config["BaseSettings"][key] = value
        self._dirty = True
        if self._callBack:
            self._callBack()

        logging.debug("SetValue: %s set to: %s", key, value)
        return True

    @property
    def dirty(self):
        return self._dirty

    @property
    def monitoring(self):
        return self._monitoring

    @monitoring.setter
    def monitoring(self, value):
        self._monitoring = value

    @property
    def sourceDir(self):
        return pathlib.Path(self._config["BaseSettings"].get("source_dir", "."))

    @sourceDir.setter
    def sourceDir(self, value):
        self.__setValue("source_dir", value)

    @property
    def fileFormat(self):
        return self._config["BaseSettings"].get("file_format", self.SHORT_FORMAT)

    @fileFormat.setter
    def fileFormat(self, value):

        if self.__setValue("file_format", value):
            logging.info("Changed filename format to %s", self.fileFormat)

    @property
    def autoStart(self):
        return self._config["BaseSettings"].getboolean("auto_start", False)

    @autoStart.setter
    def autoStart(self, value: bool):

        if self.__setValue("auto_start", str(value)):
            logging.info("Changed autostart to %s", self.autoStart)

    @property
    def logLevel(self):
        return self._config["BaseSettings"].get("loglevel", "ERROR")

    @logLevel.setter
    def logLevel(self, value):
        if self.__setValue("loglevel", value):
            if self._logFileHandler:
                self._logFileHandler.setLevel(self.logLevel)

            # Base loghandler is always lowest level
            logging.getLogger().setLevel(logging.DEBUG)
            # Widget handler should always be on INFO
            self._logHandler.setLevel(logging.INFO)
            logging.info("Altered log level to %s", self.logLevel)

    @property
    def logToFile(self):
        return self._config["BaseSettings"].getboolean("log_to_file", False)

    @logToFile.setter
    def logToFile(self, value: bool):
        if self.__setValue("log_to_file", str(value)):
            self._setFileLogging()

    def setCallBack(self, callBack):
        self._callBack = callBack

    def removeCallBack(self):
        self._callBack = None

    def setLogListener(self, logListener):
        self._logListener = logListener
        self._logHandler.set_listener(logListener)

    def removeLogListener(self):
        self._logListener = None

    def _addLogHandlerToLogger(self):
        logger = logging.getLogger()
        logger.addHandler(self._logHandler)
        logging.info("Added custom log handler for logging")

    def _setFileLogging(self):
        logger = logging.getLogger()

        if self.logToFile == 1:
            # check if there is a file handler

            file = pathlib.Path(self.LOGFILENAME).resolve()

            if file.exists():
                file.unlink()

            if not self._logFileHandler:

                self._logFileHandler = logging.FileHandler(self.LOGFILENAME)
                self._logFileHandler.setFormatter(
                    logging.Formatter(**self.FILE_LOG_FORMAT)
                )
                self._logFileHandler.setLevel(self.logLevel)
                logger.addHandler(self._logFileHandler)

                logging.info("Added file handler for logging to %s", self.LOGFILENAME)
        else:
            if self._logFileHandler:
                logger.removeHandler(self._logFileHandler)
                self._logFileHandler.flush()
                self._logFileHandler.close()
                self._logFileHandler = None
                logging.info("Removed file handler for logging")

    def save(self):
        with open(self._iniFileName, "w") as configfile:
            self._config.write(configfile)
            logging.info("Saved configurarion")
            self._dirty = False
            if self._callBack:
                self._callBack()

    # debateble if this is really af method of this class
    def newFileName(self, currentFilename):
        if self.fileFormat == self.SHORT_FORMAT:
            return pathlib.Path(currentFilename[:8] + ".xml")
        if self.fileFormat == self.ZERO_FORMAT:
            return pathlib.Path(currentFilename[:8] + "01.xml")


class loggerHandler(logging.Handler):
    def __init__(self, logLevel, formatDict):
        logging.Handler.__init__(self)
        self.setLevel(logLevel)
        self.setFormatter(logging.Formatter(**formatDict))
        self._listener = None

    # This function is called when a log message is to be handled

    def emit(self, record):
        if self._listener:
            self._listener(str(self.format(record) + "\n"))

    def set_listener(self, listener):
        self._listener = listener
