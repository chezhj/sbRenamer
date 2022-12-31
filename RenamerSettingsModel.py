import logging
import configparser
import pathlib

class RenamerSettings:

    SHORT_FORMAT = "ICAOICOA.xml"
    ZERO_FORMAT = "ICAOICOA01.xml"
    LOGLEVELS = [ "CRITICAL","ERROR","WARNING","INFO","DEBUG" ]
    FILEFORMATS = [ SHORT_FORMAT,ZERO_FORMAT ]
    LOGFILENAME = 'log.txt'


    def __init__(self, cnfFileName):
        self._config = configparser.ConfigParser()
        self._dirty = True
        if self._config.read(cnfFileName) == []:
            logging.error("No configfile (%s) found" %cnfFileName)
            exit(1) 
        self._dirty = False
        logging.basicConfig(level=self.logLevel,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
        logging.info("Configuration loaded from: %s" %cnfFileName)
        self._iniFileName = cnfFileName

    def __setValue(self, key, value):
        if value == self._config['BaseSettings'].get(key):
            return
        self._config['BaseSettings'][key]=value
        self._dirty=True
        logging.info("%s set to: %s", key ,value )

    @property
    def dirty(self):
        return self._dirty

        

    @property
    def sourceDir(self):
        return pathlib.Path(self._config['BaseSettings'].get("source_dir","."))

    @sourceDir.setter
    def sourceDir(self, value):
        self.__setValue("source_dir",value)
        

    @property
    def fileFormat(self):
        return self._config['BaseSettings'].get("file_format", self.SHORT_FORMAT)


    @fileFormat.setter
    def fileFormat(self, value):
        #todo validate at later stage
        self.__setValue("file_format",value)
    
    @property
    def logLevel(self):
        return self._config['BaseSettings'].get('loglevel', "ERROR")        

    @logLevel.setter
    def logLevel(self,value):
        self.__setValue('loglevel',value)
        logging.getLogger().setLevel(self.logLevel)
        logging.info("Altered log level to %s",self.logLevel)
    
    @property
    def logToFile(self):
        return self._config['BaseSettings'].get("log_to_file", 0)

    @logToFile.setter
    def logToFile(self, value):
        self.__setValue("log_to_file",str(value))
        self._setFileLogging()

    def _setFileLogging(self):
            logger = logging.getLogger()
            logFileHandler = None
            for lHandler  in logger.handlers:
                if lHandler.__class__.__name__ == "FileHandler":
                    logging.info("Found file handler for logging")
                    logFileHandler = lHandler

            if self.logToFile == "1":
                #check if there is a file handler
                if not logFileHandler:
                    logFileHandler = logging.FileHandler(self.LOGFILENAME)                 
                    logger.addHandler(logFileHandler)
                    logging.info("Added file handler for logging to %s", self.LOGFILENAME)
            else:
                if logFileHandler:
                    logger.removeHandler(logFileHandler)
                    logging.info("Removed file handler for logging")

    def safe(self):
        with open(self._iniFileName, 'w') as configfile:
            self._config.write(configfile)
            logging.info("Saved configurarion")
            self._dirty=False

    #debateble if this is really af method of this class
    def newFileName(self, currentFilename):
        if self.fileFormat == self.SHORT_FORMAT:
            return pathlib.Path(currentFilename[:8] + ".xml")
        if self.fileFormat == self.ZERO_FORMAT:
            return pathlib.Path(currentFilename[:8] + "01.xml")
            