
import logging
import time
import configparser
import pathlib
import shutil
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler
from RenamerSettingsModel import RenamerSettings

configFileName='config.ini'
#used python-watchdog.py from https://gist.github.com/rms1000watt



def main():
    config = configparser.ConfigParser()
    
    if config.read(configFileName) == []:
        logging.error("No configfile (%s) found" %configFileName)
        exit(1)

    loglevel=config['BaseSettings']['loglevel']
    if loglevel != "": 
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)

     
    logging.basicConfig(level=numeric_level,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    return(config)

    

def startMonitoring(config,clConfig):
    config.observer = Observer()
    sourcedir=pathlib.Path(config['BaseSettings']['source_dir'])
   
    config.observer.schedule(MyHandler(config, clConfig), sourcedir , recursive=False)
    config.observer.start() 
    logging.info(f"Starting File System Watcher")
    
def stopMonitoring(config, clConfig):    
    config.observer.stop()
    config.observer.join()

  
class MyHandler(PatternMatchingEventHandler):
    patterns = ["*.xml"]
    fileNameCreated = pathlib.Path(__file__)

    def __init__(self,config, clConfig):
        PatternMatchingEventHandler.__init__(self)
        self._config = config
        self._clConfig = clConfig

    def on_created(self, event):
        logging.info(f"created  %s" %(event.src_path))
        
        #Need to check if the file created previously supdattill exitst to prevent errors
        if self.fileNameCreated.exists():
            # Now lest check if the file that triggers the event, is the one we just created, because we
            # don't need to do anything with this file
            if self.fileNameCreated.samefile(pathlib.Path(event.src_path)) :
                logging.info("Ignoring the file just created by this process")
                return
        
        self.copy_shortend(event)
        
    def copy_shortend(self, event):
        newfilePath = pathlib.Path(event.src_path)
        filename = newfilePath.stem
        #destFile = newfilePath.parent / pathlib.Path(filename[:8] +  newfilePath.suffix)
        destFile = newfilePath.parent / self._clConfig.newFileName(filename)

        self.fileNameCreated=destFile
        if destFile.is_file():
            logging.info(f"Destination file exits" )
            backupFile = destFile.parent / pathlib.Path(destFile.stem + "_" + time.strftime("%Y%m%d%H%M%S") + destFile.suffix )
            destFile.rename(backupFile)
            logging.info(f"Renamed existing file to %s" %(backupFile) )

        shutil.copyfile(newfilePath,destFile)
        logging.info(f"filename: %s copied to %s" %(filename, destFile) )
        
class SettingView(ttk.Frame):
    
    def __init__(self, parent):
        super().__init__(parent, padding=10, width=680, height=110, relief="ridge", borderwidth=3)
        self.grid_propagate(0)

        
        #FlightPlanPath widgets
        self.lblFlightPlanPath = tk.Label(self,text="Flight Plan directory:", pady="5")
        self.lblFlightPlanPath.grid(row="0", column="0",sticky='W')
        self.strDirectory = tk.StringVar()
        entFlightPlanPath = tk.Entry(self, textvariable=self.strDirectory, width=50)
        entFlightPlanPath.grid(row="0",column="1", columnspan=3, sticky='W', padx=5)
        #Browse for dir button
        self.btnBrowser = ttk.Button(self, text="browse",
                                    command=self.getDirectory)
        self.btnBrowser.grid(row=0, column=4)
        
        #Renamer settings widgets
        self.lblFilenameFormat = tk.Label(self,text="Filename Format:", pady="5")
        self.lblFilenameFormat.grid(row="1", column="0", sticky='W')

        self.strFileFormat = tk.StringVar()
        self.ddFilenameFormat=ttk.Combobox(self, textvariable=self.strFileFormat)
        self.ddFilenameFormat.state='readonly'
        self.ddFilenameFormat.grid(row="1", column="1",sticky='W', padx=5)
        self.ddFilenameFormat.bind('<<ComboboxSelected>>', self.comboSelected)
    

        # Log settings widgets
        self.intLogToFile = tk.IntVar()
        self.cbLog2File=tk.Checkbutton(self, text='Log to file', onvalue=1, offvalue=0, variable=self.intLogToFile,
            command=self.update_model)
        self.cbLog2File.grid(row=2,column=2,sticky='W')
        self.lblLogLevel = tk.Label(self,text="Log level:", pady="5")
        self.lblLogLevel.grid(row="2", column="0", sticky='W')
        
        self.strLogLevel=tk.StringVar()
        self.lstLoglevels = []
        self.ddLogLevel=ttk.Combobox(self,textvariable=self.strLogLevel)
        self.ddLogLevel.state='readonly'
        self.ddLogLevel.grid(row="2", column="1",sticky='W', padx=5)
        self.ddLogLevel.bind('<<ComboboxSelected>>',self.comboSelected)


        #Safe button
        self.btnSafe = ttk.Button(self, text="Safe", state="disabled", command=self.safe)
        self.btnSafe.grid(row=1, column=4)
 
        self._controller =  None


    def setWidgets(self,flightPlanPath, fileFormat, fileFormatsList ):
        self.strDirectory.set(flightPlanPath)
        self.strFileFormat.set(fileFormat)
        self.ddFilenameFormat['values']=fileFormatsList

    def setLogWidgets(self,logLevel, logLevelsList, logToFile):
        self.lstLoglevels=logLevelsList
        self.ddLogLevel['values']=self.lstLoglevels
        self.strLogLevel.set(logLevel.upper())
        self.ddLogLevel.current(self.lstLoglevels.index(self.strLogLevel.get()))
        self.intLogToFile.set(logToFile)

    def getDirectory(self):
        # get a directory path by user
        selected=filedialog.askdirectory(initialdir=self.strDirectory.get(),
                                    title="Dialog box")
        if selected != "":
            self.strDirectory.set(selected)
            logging.info(f"New directory is set to:  %s" % self.strDirectory.get())
            self.update_model()
    
    def set_controller(self, controller):
        self._controller=controller

    def update_model(self):
        if self._controller:
            print(str(self.intLogToFile.get()))
            self._controller.updateModel(self.strDirectory.get(),
            self.strFileFormat.get(),
            self.strLogLevel.get(),
            self.intLogToFile.get())

    def comboSelected(self,event):
        self.update_model()

    def safe(self):
        if self._controller:
            self._controller.safe()

class Controller:
    def __init__(self, model : RenamerSettings, view):
        self.model = model
        self.view = view

    def updateModel(self, directory, fileformat, loglevel, logtofile ):
        self.model.sourceDir=directory
        self.model.fileFormat=fileformat
        self.model.logLevel=loglevel
        self.model.logToFile=logtofile

def getDirectory(strDirectory):
    # get a directory path by user
    selected=filedialog.askdirectory(initialdir=strDirectory.get(),
                                    title="Dialog box")
    if selected != "":
        strDirectory.set(selected)
        #logger = logging.getLogger(__name__)
        logging.info(f"New directory is:  %s" %strDirectory.get())
        update_model()

def Logtofile():
    logger = logging.getLogger()
    logger.info("checking")
    for lHandler  in logger.handlers:
        if lHandler.__class__.__name__ == "FileHandler":
            logger.removeHandler(lHandler)
            return

    handler = logging.FileHandler('log.txt')
    logger.addHandler(handler)

def cmdStartStop(strStartStop, config):
    print("starting or stopping")
    print(strState.get())
    
    if strStartStop.get() == "Start":
        strStartStop.set("Stop")
        startMonitoring(config,clConfig)
        return

    if strStartStop.get() == "Stop":
        strStartStop.set("Start")
        stopMonitoring(config,clConfig)

def safeSettings():
    clConfig.safe()
    if clConfig.dirty:
        btnSafe["state"]=tk.NORMAL
    else:
        btnSafe["state"]=tk.DISABLED



if __name__ == "__main__":
    config=main()
    clConfig = RenamerSettings(configFileName)
  
    logging.info("Starting up")
    root = tk.Tk()
    root.geometry("700x400")
    root.resizable(width=False,height=False)
    root.title("SimBrief Renamer by ChezHJ")

    clSettings = SettingView(root)
    clSettings.grid(column=0, row=0,padx=5,pady=5, ipadx=5)
    clSettings.setWidgets(clConfig.sourceDir,clConfig.fileFormat,clConfig.FILEFORMATS)
    clSettings.setLogWidgets(clConfig.logLevel,clConfig.LOGLEVELS,clConfig.logToFile)

    controller=Controller(clConfig,clSettings)
    clSettings.set_controller(controller)

    frmState=ttk.Frame(root, padding=15, width=680, height=100, relief="ridge", borderwidth=3)
    frmState.grid_propagate(0)
    frmState.grid(column=0, row=1,padx=5,pady=5, ipadx=5)

    strState = tk.StringVar()
    strState.set("Start")
    btnStart = ttk.Button(frmState, textvariable=strState, command=lambda: cmdStartStop(strState, config))
                                    
    print(strState.get())                               
    btnStart.grid(row=1, column=4)
 
    root.mainloop()
   