import logging
import configparser
import pathlib

class RenamerSettings:

    SHORT_FORMAT = "ICAOICOA.xml"
    ZERO_FORMAT = "ICAOICOA01.xml"
    LOGLEVELS = [ "CRITICAL","ERROR","WARNING","INFO","DEBUG" ]
    FILEFORMATS = [ SHORT_FORMAT,ZERO_FORMAT ]


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
    def logLevel(self):
        return self._config['BaseSettings'].get('loglevel', "ERROR")        

    @logLevel.setter
    def logLevel(self,value):
        self.__setValue('loglevel',value)
        

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
    def logToFile(self):
        return self._config['BaseSettings'].get("log_to_file", 0)

    @fileFormat.setter
    def logToFile(self, value):
        self.__setValue("log_to_file",value)

    def safe(self):
        with open(self._iniFileName, 'w') as configfile:
            self._config.write(configfile)
        self._dirty=False

    #debateble if this is really af method of this class
    def newFileName(self, currentFilename):
        if self.fileFormat == self.SHORT_FORMAT:
            return pathlib.Path(currentFilename[:8] + ".xml")
        if self.fileFormat == self.ZERO_FORMAT:
            return pathlib.Path(currentFilename[:8] + "01.xml")
            