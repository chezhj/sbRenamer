
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
            self.update_model()
            logging.info(f"New directory is set to:  %s" % self.strDirectory.get())
            
    
    def set_controller(self, controller):
        self._controller=controller

    def update_model(self):
        if self._controller:
            self._controller.updateModel(self.strDirectory.get(),
            self.strFileFormat.get(),
            self.strLogLevel.get(),
            self.intLogToFile.get())

    def comboSelected(self,event):
        self.update_model()

    def safe(self):
        if self._controller:
            self._controller.safe()

    def updateSafeBtn(self, dirty):
        if dirty:
            self.btnSafe["state"]=tk.NORMAL
        else:
            self.btnSafe["state"]=tk.DISABLED



class RenamerView(ttk.Frame):
    
    def __init__(self, parent):
        super().__init__(parent, padding=15, width=680, height=100, relief="ridge", borderwidth=3)
        self.grid_propagate(0)
        self.grid(column=0, row=1,padx=5,pady=5, ipadx=5)
        self.strState = tk.StringVar()
        self.strState.set("Start")
        self.btnStart = ttk.Button(self, textvariable=self.strState, command=self.startStop)
        self.btnStart.grid(row=1, column=4)
        self._controller =  None
                                    
    def startStop(self):
        if self._controller:
            newState=self._controller.switchMonitoring(self.strState.get())
            self.strState.set(newState)

    def set_controller(self, controller):
        self._controller=controller      


class Controller:
    def __init__(self, model : RenamerSettings, settingView:SettingView, renameView:RenamerView):
        self.model = model
        self.settingView = settingView
        self.renamerView = renameView
        #self.view.set_controller=self
      
        self.model.setCallBack(self.updateView)


    def updateModel(self, directory, fileformat, loglevel, logtofile ):
        self.model.sourceDir=directory
        self.model.fileFormat=fileformat
        self.model.logLevel=loglevel
        self.model.logToFile=logtofile

    def switchMonitoring(self,state):
        if state=="Stop":
            self.stopMonitoring()
            return "Start"
        else:
            self.startMonitoring()
            return "Stop"

    def startMonitoring(self):
        self._observer = Observer()
        sourcedir=pathlib.Path(self.model.sourceDir)
        self._observer.schedule(MyHandler(self.model), sourcedir , recursive=False)
        self._observer.start() 
        self.model.monitoring=True
        logging.info(f"Starting File System Watcher")

    def stopMonitoring(self):    
        self._observer.stop()
        self._observer.join()
        logging.info(f"Stopping File System Watcher")

    def safe(self):
        self.model.safe()

    def updateView(self):
        self.settingView.updateSafeBtn(self.model.dirty)

class MyHandler(PatternMatchingEventHandler):
    #Set filename pattern
    patterns = ["*.xml"]
    #Initialise fileNameCreated, will be used to ignore the file created
    fileNameCreated = pathlib.Path(__file__)

    def __init__(self, model : RenamerSettings):
        PatternMatchingEventHandler.__init__(self)
        self.model=model

    def on_created(self, event):
        logging.info(f"Found newly created file: %s" %(event.src_path))
        
        #Need to check if the file created previously still exitst to prevent errors
        if self.fileNameCreated.exists():
            logging.debug("FilenameCreated (%s) is existing", self.fileNameCreated) 
            # Now lets check if the file that triggers the event, is the one we just created, because we
            # don't need to do anything with this file
            if self.fileNameCreated.samefile(pathlib.Path(event.src_path)) :
                logging.info("Ignoring the file just created by this process")
                return
        
        self.copy_shortend(event)
        
    def copy_shortend(self, event):
        # This method needs to move to the Renamer model??
        newfilePath = pathlib.Path(event.src_path)
        filename = newfilePath.stem
        destFile = newfilePath.parent / self.model.newFileName(filename)

        self.fileNameCreated=destFile
        if destFile.is_file():
            logging.info(f"Destination file exits" )
            backupFile = destFile.parent / pathlib.Path(destFile.stem + "_" + time.strftime("%Y%m%d%H%M%S") + destFile.suffix )
            destFile.rename(backupFile)
            logging.info(f"Renamed existing file to %s" %(backupFile) )

        shutil.copyfile(newfilePath,destFile)
        logging.info(f"filename: %s copied to %s" %(filename, destFile) )


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("700x400")
        self.resizable(width=False,height=False)
        self.title("SimBrief Renamer by ChezHJ")

        self._config = RenamerSettings(configFileName)

        self._settings = SettingView(self)
        self._settings.grid(column=0, row=0,padx=5,pady=5, ipadx=5)
        self._settings.setWidgets(self._config.sourceDir,self._config.fileFormat,self._config.FILEFORMATS)
        self._settings.setLogWidgets(self._config.logLevel,self._config.LOGLEVELS,self._config.logToFile)

        self._renamerView = RenamerView(self)
        self._renamerView.grid(column=0, row=1,padx=5,pady=5, ipadx=5)
        controller=Controller(self._config,self._settings, self._renamerView)
        self._controller=controller
        self._settings.set_controller(controller)
        self._renamerView.set_controller(controller)




if __name__ == "__main__":
    
    app=MainApp()

    app.mainloop()
   