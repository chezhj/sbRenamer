"""Module for extended LoggerHandler with listerner"""
import logging


class LoggerHandler(logging.Handler):
    """Extend default handler to include listener"""

    def __init__(self, logLevel, formatDict):
        logging.Handler.__init__(self)
        self.setLevel(logLevel)
        self.setFormatter(logging.Formatter(**formatDict))
        self._listener = None

    def emit(self, record):
        # This function is called when a log message is to be handled
        if self._listener:
            self._listener(str(self.format(record) + "\n"))

    def set_listener(self, listener):
        """setter for listener"""
        self._listener = listener
