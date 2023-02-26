import logging
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog

# Mod 1.  Made filepath non editable & proper class var
#         https://github.com/chezhj/sbRenamer/issues/1
#

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
        # Mod 1
        self.entFlightPlanPath = tk.Entry(self, textvariable=self.strDirectory, width=62)
        self.entFlightPlanPath.config(state='readonly')
        self.entFlightPlanPath.grid(row="0",column="1", columnspan=3, sticky='W', padx=5)

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