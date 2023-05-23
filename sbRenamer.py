from datetime import datetime
import logging
import sys
import threading
import time
import pathlib
import shutil
import tkinter as tk
from tkinter import messagebox
from pystray import MenuItem as item
import pystray


from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from RenamerSettingsModel import RenamerSettings
from tkinter.messagebox import showerror
from RenamerViews import RenamerView, SettingView
from PIL import Image, ImageTk

configFileName = "config.ini"
# used python-watchdog.py from https://gist.github.com/rms1000watt
# and http://sfriederichs.github.io/how-to/python/gui/logging/2017/12/21/Python-GUI-Logging.html
# and mvc intro https://www.pythontutorial.net/tkinter/tkinter-mvc/
# and system try https://www.tutorialspoint.com/how-to-make-a-system-tray-application-in-tkinter#


# Mod 10 20230523 Added notification while in system tray, solves issue 8
# Mod 11 20230523 Added optional restart of the listner after save


class Controller:
    def __init__(
        self, model: RenamerSettings, settingView: SettingView, renameView: RenamerView
    ):
        self.model = model
        self.settingView = settingView
        self.renamerView = renameView
        # Mod 8 Added listener prop to store listerer to activate on rename
        self.listener = None
        # self.view.set_controller=self

        self.model.setCallBack(self.updateView)
        self.model.setLogListener(self.updateWidget)
        if self.model.autoStart:
            logging.info("Auto starting watcher in 3 seconds")
            self.renamerView.after(3000, self.renamerView.startStop)
        if self.model.autoHide:
            logging.info("Auto hiding into system tray in 5 seconds")
            self.renamerView.after(5000, self.renamerView.minimize)

    def updateModel(
        self,
        directory,
        fileformat,
        loglevel,
        logtofile,
        autoStart: bool,
        autoHide: bool,
    ):
        self.model.sourceDir = directory
        self.model.fileFormat = fileformat
        self.model.logLevel = loglevel
        self.model.logToFile = logtofile
        self.model.autoStart = autoStart
        self.model.autoHide = autoHide

    def switchMonitoring(self, state):
        if state == "Stop":
            self.stopMonitoring()
            return "Start"
        else:
            self.startMonitoring()
            return "Stop"

    def startMonitoring(self):
        self._observer = Observer()
        sourcedir = pathlib.Path(self.model.sourceDir)
        self._observer.schedule(
            # Mod 10 Create Handler with internal listener
            MyHandler(self.model, self.listenerWrap),
            sourcedir,
            recursive=False,
        )
        self._observer.daemon = True
        self._observer.start()

        self.model.monitoring = True
        logging.info(f"Starting File System Watcher")

    def stopMonitoring(self):
        self._observer.stop()
        self._observer.join()
        self.model.monitoring = False
        logging.info(f"Stopping File System Watcher")

    def isMonitoring(self) -> bool:
        return self.model.monitoring

    # 10 Listerner Wrapper
    def listenerWrap(self, message, title):
        if self.listener:
            self.listener(message, title)

    def isActiveMonitoring(self) -> bool:
        if self._observer:
            return self._observer.is_alive()
        else:
            logging.warning("Observer is no longer present")
            return False

    # 10 Set listener prop
    def setListener(self, listener):
        self.listener = listener

    def save(self):
        self.model.save()
        # 11 If monitoring is active ask the user if he wants to restart
        if self.isMonitoring():
            if messagebox.askyesno(
                title="sbRenamer",
                message="Restart listener to use new settings?",
            ):
                self.stopMonitoring()
                self.startMonitoring()

    def updateView(self):
        self.settingView.updateSaveBtn(self.model.dirty)

    def updateWidget(self, value):
        self.renamerView.addLine(value)


class MyHandler(PatternMatchingEventHandler):
    # Set filename pattern
    patterns = ["*.xml"]
    # Initialise fileNameCreated, will be used to ignore the file created
    fileNameCreated = pathlib.Path(__file__)

    # 10 Added listener on construct
    def __init__(self, model: RenamerSettings, listener):
        PatternMatchingEventHandler.__init__(self)
        self.model = model
        self.listener = listener

    def on_created(self, event):
        logging.info(f"Found newly created file: %s" % (event.src_path))

        # Need to check if the file created previously still exitst to prevent errors
        if self.fileNameCreated.exists():
            logging.debug("FilenameCreated (%s) is existing", self.fileNameCreated)
            # Now lets check if the file that triggers the event, is the one we just created, because we
            # don't need to do anything with this file
            if self.fileNameCreated.samefile(pathlib.Path(event.src_path)):
                logging.info("Ignoring the file just created by this process")
                return

        self.copy_shortend(event)

    def copy_shortend(self, event):
        # This method needs to move to the Renamer model??
        logging.debug("Start copy")
        newfilePath = pathlib.Path(event.src_path)
        filename = newfilePath.stem
        # 10 Change destFile into Path, to use pathib functions
        destFile = pathlib.Path(newfilePath.parent / self.model.newFileName(filename))

        self.fileNameCreated = destFile
        if destFile.is_file():
            logging.info(f"Destination file exits")
            backupFile = destFile.parent / pathlib.Path(
                destFile.stem + "_" + time.strftime("%Y%m%d%H%M%S") + destFile.suffix
            )
            destFile.rename(backupFile)
            logging.info(f"Renamed existing file to %s" % (backupFile))

        try:
            shutil.copyfile(newfilePath, destFile)
            logging.info(f"filename: %s copied to %s" % (filename, destFile))
            # 10 If the listener is assigned, activate it with correct message
            if self.listener:
                self.listener(
                    f"filename: %s copied to %s" % (filename, destFile.name),
                    "sbRenamer",
                )

        except Exception as err:
            logging.error(
                f"Unable to copy %s to %s, error: %s" % (filename, destFile, err)
            )


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("620x560")
        self.resizable(width=False, height=False)

        self.title("SimBrief Renamer by ChezHJ")
        self.iconbitmap("./sbRenamer.ico")
        # if we want parent frames to resize to there master, we need to update the app
        self.update()

        self._settings = SettingView(self)
        self._settings.grid(column=0, row=0, padx=5, pady=5, ipadx=5)

        self._renamerView = RenamerView(self)
        self._renamerView.grid(column=0, row=1, padx=5, pady=5, ipadx=5)

        self._config = RenamerSettings(configFileName)
        controller = Controller(self._config, self._settings, self._renamerView)

        # should move to controller?
        self._settings.setWidgets(
            self._config.sourceDir,
            self._config.fileFormat,
            self._config.FILEFORMATS,
            self._config.autoStart,
            self._config.autoHide,
        )
        self._settings.setLogWidgets(
            self._config.logLevel, self._config.LOGLEVELS, self._config.logToFile
        )

        self._controller = controller
        self._settings.set_controller(controller)
        self._renamerView.set_controller(controller)

        self.bind("<Unmap>", self._resize_handler)

        self.hidden = False
        logging.info("Succesfully initialised")

    def _resize_handler(self, event):
        self._minimizeEvent = False
        for key in dir(event):
            if not key.startswith("_"):
                savedAttr = getattr(event, key)

                if key == "widget" and isinstance(savedAttr, tk.Tk):
                    if getattr(event, "type") == "18":
                        self._minimizeEvent = True
        if self._minimizeEvent:
            self.hide_window(event)
        return

    def hide_window_exit(self):
        self.hide_window(None)

    def hide_window(self, event):
        if self.hidden:
            return
        self.hidden = True
        self.withdraw()
        self.image = Image.open("./sbRenamer.ico")
        self.menu = (
            item("Quit", self.quit_window),
            item("Show", default=True, action=self.show_window),
        )

        self.icon = pystray.Icon("name", self.image, "Simbrief Renamer", self.menu)
        # 10 Set listener
        self._controller.setListener(self.icon.notify)
        # Fixing issue 7, by starting the icon in a separate thread, not blocking other actions
        # Used to be self.icon.run()
        threading.Thread(target=self.icon.run).start()

        return

    def show_window(self, item):
        self.icon.stop()
        self.hidden = False
        self.deiconify()

    def close(self):
        if self._controller.isActiveMonitoring():
            logging.info("Stopping monitoring first")
            self._controller.stopMonitoring()
        self.destroy()

    def quit_window(self, item):
        self.icon.stop()
        self.close()


if __name__ == "__main__":
    try:
        app = MainApp()
    except FileNotFoundError as e:
        showerror("Error", e.filename + "\n" + e.strerror)
        sys.exit(1)

    app.mainloop()
