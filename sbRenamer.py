
from datetime import datetime
import logging
import sys
import time
import configparser
import pathlib
import shutil
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import scrolledtext
from watchdog.observers import Observer  
from watchdog.events import PatternMatchingEventHandler
from RenamerSettingsModel import RenamerSettings
from tkinter.messagebox import showerror

configFileName='config.ini'
#used python-watchdog.py from https://gist.github.com/rms1000watt
#and http://sfriederichs.github.io/how-to/python/gui/logging/2017/12/21/Python-GUI-Logging.html
#and mvc intro https://www.pythontutorial.net/tkinter/tkinter-mvc/


 
        
class SettingView(ttk.Frame):
    
    def __init__(self, parent):
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        super().__init__(parent, padding=10, width=parent_width-22, height=110, relief="ridge", borderwidth=3)
        self.grid_propagate(0)

        
        #FlightPlanPath widgets
        self.lblFlightPlanPath = tk.Label(self,text="Flight Plan directory:", pady="5")
        self.lblFlightPlanPath.grid(row="0", column="0",sticky='W')
        self.strDirectory = tk.StringVar()
        entFlightPlanPath = tk.Entry(self, textvariable=self.strDirectory, width=62)
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
       
        self.ddFilenameFormat.config(state='readonly' )
        self.ddFilenameFormat.grid(row="1", column="1",sticky='W', padx=5)
        self.ddFilenameFormat.bind('<<ComboboxSelected>>', self.comboSelected)
    
        self.lblAutoStart = tk.Label(self, text="Auto start:")
        self.lblAutoStart.grid(row="1", column="2",sticky='W')
        
        self.intAutoStart = tk.IntVar()
        self.cbAutoStart=tk.Checkbutton(self, onvalue=1, offvalue=0, variable=self.intAutoStart,
            command=self.update_model)
        self.cbAutoStart.grid(row=1,column=3,sticky='W')


      

        # Log settings widgets
        self.lblLogToFile = tk.Label(self,text='Log to file:')
        self.lblLogToFile.grid(row="2",column="0",sticky='W')

        self.intLogToFile = tk.IntVar()
        self.cbLog2File=tk.Checkbutton(self, text='Active', onvalue=1, offvalue=0, variable=self.intLogToFile,
            command=self.update_model)
        self.cbLog2File.grid(row=2,column=1,sticky='W')
        self.lblLogLevel = tk.Label(self,text="Log level:", pady="5")
        self.lblLogLevel.grid(row="2", column="2", sticky='W')
        
        self.strLogLevel=tk.StringVar()
        self.lstLoglevels = []
        self.ddLogLevel=ttk.Combobox(self,textvariable=self.strLogLevel)
        self.ddLogLevel.config(state='readonly')
        self.ddLogLevel.grid(row="2", column="3",sticky='W', padx=5)
        self.ddLogLevel.bind('<<ComboboxSelected>>',self.comboSelected)


        #Save button
        self.btnSave = ttk.Button(self, text="Save", state="disabled", command=self.save)
        self.btnSave.grid(row=1, column=4)
 
        self._controller =  None


    def setWidgets(self,flightPlanPath, fileFormat, fileFormatsList, autoStart:int):
        self.strDirectory.set(flightPlanPath)
        self.strFileFormat.set(fileFormat)
        self.ddFilenameFormat['values']=fileFormatsList
        
        self.intAutoStart.set(autoStart)

    def setLogWidgets(self,logLevel, logLevelsList, logToFile):
        self.lstLoglevels=logLevelsList
        self.ddLogLevel['values']=self.lstLoglevels
        self.strLogLevel.set(logLevel.upper())
     
        self.update_loglevelwidget(logToFile)

        self.ddLogLevel.current(self.lstLoglevels.index(self.strLogLevel.get()))
        self.intLogToFile.set(logToFile)
        

    def update_loglevelwidget(self, logToFile):
        if logToFile == 1:
            self.ddLogLevel.config(state='readonly')
        else:
            self.ddLogLevel.config(state='disabled')

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
            self.intLogToFile.get(), self.intAutoStart.get())
        self.update_loglevelwidget(self.intLogToFile.get())

    def comboSelected(self,event):
        self.update_model()

    def save(self):
        if self._controller:
            self._controller.save()

    def updateSaveBtn(self, dirty):
        if dirty:
            self.btnSave["state"]=tk.NORMAL
        else:
            self.btnSave["state"]=tk.DISABLED



class RenamerView(ttk.Frame):
    
    def __init__(self, parent):
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        super().__init__(parent, padding=10, width=parent_width-22, height=parent_height-150, relief="ridge", borderwidth=3)
        self.grid_propagate(0)
        self.grid(column=0, row=1, sticky="NW")
        self.strState = tk.StringVar()
        self.strState.set("Start")
        self.btnStart = ttk.Button(self, textvariable=self.strState, command=self.startStop)
        self.btnStart.grid(row=1, column=3,pady=3, sticky='E')
        self.logWidget = scrolledtext.ScrolledText(self, font =("Courier",8))
        self.logWidget.config(state='disabled')
        self.logWidget.grid(row=2 ,column=0, columnspan=4,sticky='NE')
        self._controller =  None
                                    
    def startStop(self):
        if self._controller:
            newState=self._controller.switchMonitoring(self.strState.get())
            self.strState.set(newState)

    def set_controller(self, controller):
        self._controller=controller      
    
    def addLine(self,value):
        #Enable the widget to allow new text to be inserted
        self.logWidget.config(state='normal')
        
        # Append log message to the widget
        self.logWidget.insert(tk.END, value)
        
        #Scroll down to the bottom of the ScrolledText box to ensure the latest log message
        #is visible
        self.logWidget.see("end")
        
        #Re-disable the widget to prevent users from entering text
        self.logWidget.config(state='disabled')

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
   