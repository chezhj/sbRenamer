
from datetime import datetime
import logging
import sys
import time
import pathlib
import shutil
import tkinter as tk

from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler
from RenamerSettingsModel import RenamerSettings
from tkinter.messagebox import showerror
from RenamerViews import RenamerView, SettingView

configFileName='config.ini'
#used python-watchdog.py from https://gist.github.com/rms1000watt
#and http://sfriederichs.github.io/how-to/python/gui/logging/2017/12/21/Python-GUI-Logging.html
#and mvc intro https://www.pythontutorial.net/tkinter/tkinter-mvc/


class Controller:
    def __init__(self, model : RenamerSettings, settingView:SettingView, renameView:RenamerView):
        self.model = model
        self.settingView = settingView
        self.renamerView = renameView
        #self.view.set_controller=self
      
        self.model.setCallBack(self.updateView)
        self.model.setLogListener(self.updateWidget)
        if self.model.autoStart == 1:
            logging.info("Auto starting watcher in 3 seconds")
            self.renamerView.after(3000, self.renamerView.startStop)
   

    def updateModel(self, directory, fileformat, loglevel, logtofile , autoStart:int):
        self.model.sourceDir=directory
        self.model.fileFormat=fileformat
        self.model.logLevel=loglevel
        self.model.logToFile=logtofile
        self.model.autoStart=autoStart

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

    def save(self):
        self.model.save()

    def updateView(self):
        self.settingView.updateSaveBtn(self.model.dirty)
    
    def updateWidget(self, value):
        self.renamerView.addLine(value)

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
        self.geometry("620x560")
        self.resizable(width=False,height=False)
        self.title("SimBrief Renamer by ChezHJ")
        self.iconbitmap('./sbRenamer.ico')
        #if we want parent frames to resize to there master, we need to update the app
        self.update()
       
        self._settings = SettingView(self)
        self._settings.grid(column=0, row=0,padx=5,pady=5, ipadx=5)
    
        self._renamerView = RenamerView(self)
        self._renamerView.grid(column=0, row=1,padx=5,pady=5, ipadx=5)
      
        self._config = RenamerSettings(configFileName)
        controller=Controller(self._config,self._settings, self._renamerView)

        #should move to controller?
        self._settings.setWidgets(self._config.sourceDir,self._config.fileFormat,self._config.FILEFORMATS,self._config.autoStart)
        self._settings.setLogWidgets(self._config.logLevel,self._config.LOGLEVELS,self._config.logToFile)
  
        self._controller=controller
        self._settings.set_controller(controller)
        self._renamerView.set_controller(controller)

        logging.info("Succesfully initialised")


if __name__ == "__main__":
    try:
        app=MainApp()
    except FileNotFoundError as e:
        showerror("Error", e.filename +"\n" + e.strerror)
        sys.exit(1)
    app.mainloop()
   