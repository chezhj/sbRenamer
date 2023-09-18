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
from renamer_settings_model import RenamerSettings
from tkinter.messagebox import showerror
from RenamerViews import RenamerView, SettingView
from PIL import Image

configFileName = "config.ini"
# used python-watchdog.py from https://gist.github.com/rms1000watt
# and http://sfriederichs.github.io/how-to/python/gui/logging/2017/12/21/Python-GUI-Logging.html
# and mvc intro https://www.pythontutorial.net/tkinter/tkinter-mvc/
# and system try https://www.tutorialspoint.com/how-to-make-a-system-tray-application-in-tkinter#


# Mod 10 20230523 Added notification while in system tray, solves issue 8
# Mod 11 20230523 Added optional restart of the listner after save
# Mod 12 20230912 Added daemon to minimized icon thread


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
        self._observer = None

        self.model.set_callback(self.updateView)
        self.model.set_log_listener(self.updateWidget)
        if self.model.auto_start:
            logging.info("Auto starting watcher in 3 seconds")
            self.renamerView.after(3000, self.renamerView.startStop)
        if self.model.auto_hide:
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
        save_xml: bool,
    ):
        self.model.source_dir = directory
        self.model.file_format = fileformat
        self.model.log_level = loglevel
        self.model.log_to_file = logtofile
        self.model.auto_start = autoStart
        self.model.auto_hide = autoHide
        self.model.save_xml = save_xml

    def switchMonitoring(self, state):
        if state == "Stop":
            self.stopMonitoring()
            return "Start"
        else:
            self.startMonitoring()
            return "Stop"

    def startMonitoring(self):
        self._observer = Observer()
        sourcedir = pathlib.Path(self.model.source_dir)
        self._observer.schedule(
            # Mod 10 Create Handler with internal listener
            MyHandler(self.model, self.listenerWrap),
            sourcedir,
            recursive=False,
        )
        self._observer.daemon = True
        self._observer.start()

        self.model.monitoring = True
        logging.info("Starting File System Watcher")

    def stopMonitoring(self):
        self._observer.stop()
        self._observer.join()
        self.model.monitoring = False
        logging.info("Stopping File System Watcher")

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
        logging.info("Found newly created file: %s", (event.src_path))

        # Need to check if the file created previously still exitst to prevent errors
        if self.fileNameCreated.exists():
            logging.debug("FilenameCreated (%s) is existing", self.fileNameCreated)
            # Now lets check if the file that triggers the event, is the one we just created,
            # because we don't need to do anything with this file
            if self.fileNameCreated.samefile(pathlib.Path(event.src_path)):
                logging.info("Ignoring the file just created by this process")
                return
        if self.model.save_xml:
            self.copy_shortend(event)
        else:
            self.rename_shortend(event)

    def copy_shortend(self, event):
        # This method needs to move to the Renamer model??
        logging.debug("Start copy")
        newfilePath = pathlib.Path(event.src_path)
        filename = newfilePath.stem
        # 10 Change destFile into Path, to use pathib functions
        destFile = pathlib.Path(newfilePath.parent / self.model.new_filename(filename))

        self.fileNameCreated = destFile
        if destFile.is_file():
            logging.info("Destination file exits")
            self.rename_existing_file(destFile)

        try:
            shutil.copyfile(newfilePath, destFile)
            logging.info("filename: %s copied to %s", filename, destFile)
            # 10 If the listener is assigned, activate it with correct message
            if self.listener:
                self.listener(
                    f"filename: {filename} copied to {destFile.name}",
                    "sbRenamer",
                )

        except shutil.Error as err:
            logging.error("Unable to copy %s to %s, error: %s", filename, destFile, err)

    def rename_shortend(self, event):
        """Handle file created event by renaming the file that was created"""
        # This method needs to move to the Renamer model??
        logging.debug("Start rename")
        new_file_path = pathlib.Path(event.src_path)
        filename = new_file_path.stem
        # 10 Change destFile into Path, to use pathib functions
        dest_file = pathlib.Path(
            new_file_path.parent / self.model.new_filename(filename)
        )
        # keep the new file to be created to check new event
        self.fileNameCreated = dest_file
        if dest_file.is_file():
            logging.info("Destination file exits")
            self.rename_existing_file(dest_file)

        try:
            new_file_path.rename(dest_file)
            logging.info("filename: %s renamed to %s", filename, dest_file)
            # 10 If the listener is assigned, activate it with correct message
            if self.listener:
                self.listener(
                    f"filename: {filename} renamed to {dest_file.name}",
                    "sbRenamer",
                )

        except OSError as err:
            logging.error(
                "Unable to rename %s to %s, error: %s", filename, dest_file, err
            )

    def rename_existing_file(self, file_to_rename):
        """renames file to samename with datetime"""

        logging.info("Renaming file to datetime version")
        backup_file = file_to_rename.parent / pathlib.Path(
            file_to_rename.stem
            + "_"
            + time.strftime("%Y%m%d%H%M%S")
            + file_to_rename.suffix
        )
        try:
            file_to_rename.rename(backup_file)
        except OSError as error:
            logging.error("problem with renaming existing file")
            logging.error(error)
            sys.exit(1)
        logging.info("Renamed existing file to %s", backup_file)


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
            self._config.source_dir,
            self._config.file_format,
            self._config.FILEFORMATS,
            self._config.auto_start,
            self._config.auto_hide,
        )
        self._settings.set_delete_widgets(
            self._config.save_xml,
        )

        self._settings.setLogWidgets(
            self._config.log_level, self._config.LOGLEVELS, self._config.log_to_file
        )

        self._controller = controller
        self._settings.set_controller(controller)
        self._renamerView.set_controller(controller)

        self.bind("<Unmap>", self._resize_handler)

        self.hidden = False
        self.icon = None
        logging.info("Succesfully initialised")

    def _resize_handler(self, event):
        minimize_event = False
        for key in dir(event):
            if not key.startswith("_"):
                savedAttr = getattr(event, key)

                if key == "widget" and isinstance(savedAttr, tk.Tk):
                    if getattr(event, "type") == "18":
                        minimize_event = True
        if minimize_event:
            self.hide_window()
        return

    def hide_window_exit(self):
        self.hide_window()

    def hide_window(self):
        if self.hidden:
            return
        self.hidden = True
        self.withdraw()
        icon_image = Image.open("./sbRenamer.ico")
        icon_menu = (
            item("Quit", self.quit_window),
            item("Show", default=True, action=self.show_window),
        )

        self.icon = pystray.Icon("name", icon_image, "Simbrief Renamer", icon_menu)
        # 10 Set listener
        self._controller.setListener(self.icon.notify)
        # Fixing issue 7, by starting the icon in a separate thread, not blocking other actions
        # Used to be self.icon.run()
        # Mod 13
        threading.Thread(daemon=True, target=self.icon.run).start()

        return

    def show_window(self):
        self.icon.stop()
        self.hidden = False
        self.deiconify()

    def close(self):
        if self._controller.isActiveMonitoring():
            logging.info("Stopping monitoring first")
            self._controller.stopMonitoring()
        self.destroy()

    def quit_window(self):
        self.icon.stop()
        self.close()


if __name__ == "__main__":
    try:
        app = MainApp()
    except FileNotFoundError as e:
        showerror("Error", e.filename + "\n" + e.strerror)
        sys.exit(1)

    app.mainloop()
