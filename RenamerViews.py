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
        # parent_height = parent.winfo_height()
        super().__init__(
            parent,
            padding=10,
            width=parent_width - 22,
            height=140,
            relief="ridge",
            borderwidth=3,
        )
        self.grid_propagate(0)

        # FlightPlanPath widgets
        self.lblFlightPlanPath = tk.Label(self, text="Flight Plan directory:", pady="5")
        self.lblFlightPlanPath.grid(row="0", column="0", sticky="W")
        self.strDirectory = tk.StringVar()
        # Mod 1
        self.entFlightPlanPath = tk.Entry(
            self, textvariable=self.strDirectory, width=62
        )
        self.entFlightPlanPath.config(state="readonly")
        self.entFlightPlanPath.grid(
            row="0", column="1", columnspan=3, sticky="W", padx=5
        )

        # Browse for dir button
        self.btnBrowser = ttk.Button(self, text="browse", command=self.getDirectory)
        self.btnBrowser.grid(row=0, column=4)

        # Renamer settings widgets
        self.lblFilenameFormat = tk.Label(self, text="Filename Format:", pady="5")
        self.lblFilenameFormat.grid(row="1", column="0", sticky="W")

        self.strFileFormat = tk.StringVar()
        self.ddFilenameFormat = ttk.Combobox(self, textvariable=self.strFileFormat)

        self.ddFilenameFormat.config(state="readonly")
        self.ddFilenameFormat.grid(row="1", column="1", sticky="W", padx=5)
        self.ddFilenameFormat.bind("<<ComboboxSelected>>", self.comboSelected)

        self.lblAutoStart = tk.Label(self, text="Auto start:")
        self.lblAutoStart.grid(row="1", column="2", sticky="W")

        self.boolAutoStart = tk.BooleanVar()
        self.cbAutoStart = tk.Checkbutton(
            self,
            onvalue=True,
            offvalue=False,
            variable=self.boolAutoStart,
            command=self.update_model,
        )
        self.cbAutoStart.grid(row=1, column=3, sticky="W")

        self.lblAutoHide = tk.Label(self, text="Auto hide:")
        self.lblAutoHide.grid(row="1", column="3")

        self.boolAutoHide = tk.BooleanVar()
        self.cbAutoHide = tk.Checkbutton(
            self,
            onvalue=True,
            offvalue=False,
            variable=self.boolAutoHide,
            command=self.update_model,
        )
        self.cbAutoHide.grid(row=1, column=3, sticky="E")

        # Delete setting
        delete_row = 2

        self.lbl_save_xml = tk.Label(self, text="Save original XML:")
        self.lbl_save_xml.grid(row=delete_row, column="0", sticky="W")

        self.bool_save_xml = tk.BooleanVar()
        self.cb_save_xml = tk.Checkbutton(
            self,
            onvalue=True,
            offvalue=False,
            variable=self.bool_save_xml,
            command=self.update_model,
        )
        self.cb_save_xml.grid(row=delete_row, column=1, sticky="W")

        self.lbl_delete_files = tk.Label(self, text="Delete files older then (days):")
        self.lbl_delete_files.grid(row=delete_row, column="2", columnspan=2, sticky="W")

        self.nof_days = tk.StringVar()
        self.nof_days.trace_add("write", self.update_model)

        # Register validation function so only numbers can be set
        validation = self.register(self.only_numbers)
        self.ent_nof_days = tk.Entry(
            self,
            validate="key",
            validatecommand=(validation, "%S"),
            textvariable=self.nof_days,
            width=5,
        )

        self.ent_nof_days.grid(row=delete_row, column=3, sticky="E", padx=8)

        # Log settings widgets
        log_row = 3
        self.lblLogToFile = tk.Label(self, text="Log to file:")

        self.lblLogToFile.grid(row=log_row, column="0", sticky="W")

        self.boolLogToFile = tk.BooleanVar()
        self.cbLog2File = tk.Checkbutton(
            self,
            text="Active",
            onvalue=1,
            offvalue=0,
            variable=self.boolLogToFile,
            command=self.update_model,
        )
        self.cbLog2File.grid(row=log_row, column=1, sticky="W")
        self.lblLogLevel = tk.Label(self, text="Log level:", pady="5")
        self.lblLogLevel.grid(row=log_row, column="2", sticky="W")

        self.strLogLevel = tk.StringVar()
        self.lstLoglevels = []
        self.ddLogLevel = ttk.Combobox(self, textvariable=self.strLogLevel, width=22)
        self.ddLogLevel.config(state="readonly")
        self.ddLogLevel.grid(row=log_row, column="3", sticky="W", padx=5)
        self.ddLogLevel.bind("<<ComboboxSelected>>", self.comboSelected)

        # Save button
        self.btnSave = ttk.Button(
            self, text="Save", state="disabled", command=self.save
        )
        self.btnSave.grid(row=1, column=4)

        self._controller = None

    def only_numbers(self, char):
        if char:
            return char.isdigit()
        else:
            return True

    def setWidgets(
        self,
        flightPlanPath,
        fileFormat,
        fileFormatsList,
        autoStart: bool,
        autoHide: bool,
    ):
        self.strDirectory.set(flightPlanPath)
        self.strFileFormat.set(fileFormat)
        self.ddFilenameFormat["values"] = fileFormatsList

        self.boolAutoStart.set(autoStart)
        self.boolAutoHide.set(autoHide)

    def set_delete_widgets(self, save_xml, nof_days):
        """update delete widgets"""
        self.bool_save_xml.set(save_xml)
        self.nof_days.set(nof_days)

    def setLogWidgets(self, logLevel, logLevelsList, logToFile):
        self.lstLoglevels = logLevelsList
        self.ddLogLevel["values"] = self.lstLoglevels
        self.strLogLevel.set(logLevel.upper())

        self.update_loglevelwidget(logToFile)

        self.ddLogLevel.current(self.lstLoglevels.index(self.strLogLevel.get()))
        self.boolLogToFile.set(logToFile)

    def update_loglevelwidget(self, logToFile):
        if logToFile:
            self.ddLogLevel.config(state="readonly")
        else:
            self.ddLogLevel.config(state="disabled")

    def getDirectory(self):
        # get a directory path by user
        selected = filedialog.askdirectory(
            initialdir=self.strDirectory.get(), title="Dialog box"
        )
        if selected != "":
            self.strDirectory.set(selected)
            self.update_model()
            logging.info("New directory is set to:  %s", self.strDirectory.get())

    def set_controller(self, controller):
        self._controller = controller

    def update_model(self, *args):
        if self._controller:
            self._controller.update_model(
                self.strDirectory.get(),
                self.strFileFormat.get(),
                self.strLogLevel.get(),
                self.boolLogToFile.get(),
                self.boolAutoStart.get(),
                self.boolAutoHide.get(),
                self.bool_save_xml.get(),
                self.nof_days.get(),
            )
        self.update_loglevelwidget(self.boolLogToFile.get())

    def comboSelected(self, *args):
        self.update_model()

    def save(self):
        if self._controller:
            self._controller.save()

    def updateSaveBtn(self, dirty):
        if dirty:
            self.btnSave["state"] = tk.NORMAL
        else:
            self.btnSave["state"] = tk.DISABLED


class RenamerView(ttk.Frame):
    def __init__(self, parent):
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        super().__init__(
            parent,
            padding=10,
            width=parent_width - 22,
            height=parent_height - 150,
            relief="ridge",
            borderwidth=3,
        )
        self.__parent = parent
        self.grid_propagate(0)
        self.grid(column=0, row=1, sticky="NW")
        self.strState = tk.StringVar()
        self.strState.set("Start")
        self.btnStart = ttk.Button(
            self, textvariable=self.strState, command=self.startStop
        )
        self.btnStart.grid(row=1, column=3, pady=3, sticky="E")
        self.logWidget = scrolledtext.ScrolledText(self, font=("Courier", 8))
        self.logWidget.config(state="disabled")
        self.logWidget.grid(row=2, column=0, columnspan=4, sticky="NE")
        self._controller = None

    def startStop(self):
        if self._controller:
            newState = self._controller.switch_monitoring(self.strState.get())
            self.strState.set(newState)

    def set_controller(self, controller):
        self._controller = controller

    def addLine(self, value):
        # Enable the widget to allow new text to be inserted
        self.logWidget.config(state="normal")

        # Append log message to the widget
        self.logWidget.insert(tk.END, value)

        # Scroll down to the bottom of the ScrolledText box to ensure the latest log message
        # is visible
        self.logWidget.see("end")

        # Re-disable the widget to prevent users from entering text
        self.logWidget.config(state="disabled")

    def minimize(self):
        self.__parent.iconify()
