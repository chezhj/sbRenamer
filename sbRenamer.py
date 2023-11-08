"""Main module, includes controller, eventhandler and main app"""
import datetime
import logging
import os
import sys
import threading
import time
import pathlib
import shutil
import tkinter as tk
from collections.abc import Iterator
from tkinter import messagebox
from tkinter.messagebox import showerror
from pystray import MenuItem as item
import pystray

from PIL import Image

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from renamer_settings_model import RenamerSettings
from RenamerViews import RenamerView, SettingView
from _version import __version__

CONFIGFILENAME = "config.ini"
# used python-watchdog.py from https://gist.github.com/rms1000watt
# and http://sfriederichs.github.io/how-to/python/gui/logging/2017/12/21/Python-GUI-Logging.html
# and mvc intro https://www.pythontutorial.net/tkinter/tkinter-mvc/
# and system try https://www.tutorialspoint.com/how-to-make-a-system-tray-application-in-tkinter#


# Mod 10 20230523 Added notification while in system tray, solves issue 8
# Mod 11 20230523 Added optional restart of the listner after save
# Mod 12 20230912 Added daemon to minimized icon thread
# Mod 13          Actualy delete a file iso renaming
# Mod 14 20231025 Add Removing old files
# Mod 15 20231102 New filename & fms listener
# Mod 16 20231108 Added check if source is destination


class Controller:
    """class to orchestrate actions based on the model and user actions in the views"""

    def __init__(
        self,
        model: RenamerSettings,
        setting_view: SettingView,
        rename_view: RenamerView,
    ):
        self.model = model
        self.setting_view = setting_view
        self.renamer_view = rename_view
        # Mod 8 Added listener prop to store listerer to activate on rename
        self.listener = None
        # self.view.set_controller=self
        self._observer = None

        self._filedeleter = FileDeleter(
            self.model.source_dir, self.model.number_of_days
        )

        self.model.set_callback(self.update_view)
        self.model.set_log_listener(self.update_widget)
        if self.model.auto_start:
            logging.info("Auto starting watcher in 3 seconds")
            self.renamer_view.after(3000, self.renamer_view.startStop)
        if self.model.auto_hide:
            logging.info("Auto hiding into system tray in 5 seconds")
            self.renamer_view.after(5000, self.renamer_view.minimize)

        self.create_delete_thread()

    def create_delete_thread(self):
        """Creates a no deamon thread to start removing files in 10 sec"""
        self.delete_thread = threading.Timer(10, self.start_clean)
        self.delete_thread.start()

    def update_model(
        self,
        directory,
        fileformat,
        loglevel,
        logtofile,
        auto_start: bool,
        auto_hide: bool,
        save_xml: bool,
        nof_days,
        fmsformat,
    ):
        """Method that should be called to update the model"""
        self.model.source_dir = directory
        self.model.file_format = fileformat
        self.model.log_level = loglevel
        self.model.log_to_file = logtofile
        self.model.auto_start = auto_start
        self.model.auto_hide = auto_hide
        self.model.save_xml = save_xml
        self.model.number_of_days = nof_days
        self.model.fms_format = fmsformat

    def start_clean(self):
        """Start the actual deletion fot files"""
        self._filedeleter.list_files()

    def switch_monitoring(self, state):
        """Alternate monitoring based on given state"""

        if state == "Stop":
            self.stop_monitoring()
            return "Start"
        # else:
        self.start_monitoring()
        return "Stop"

    def start_monitoring(self):
        """Starts a new observer as deamon whith a the custom rename/delete handler"""

        self._observer = Observer()
        sourcedir = pathlib.Path(self.model.source_dir)
        self._observer.schedule(
            # Mod 10 Create Handler with internal listener
            RenameXmlHandler(self.model, self.listener_wrap),
            sourcedir,
            recursive=False,
        )
        self._observer.daemon = True
        self._observer.start()

        self.model.monitoring = True
        logging.info("Starting File System Watcher")

    def stop_monitoring(self):
        """Stops the monitoring thread"""

        self._observer.stop()
        self._observer.join()
        self.model.monitoring = False
        logging.info("Stopping File System Watcher")

    def is_monitoring(self) -> bool:
        """Returns monitoring model state"""

        return self.model.monitoring

    # 10 Listerner Wrapper
    def listener_wrap(self, message, title):
        """method to call listener if set"""
        if self.listener:
            self.listener(message, title)

    def is_active_monitoring(self) -> bool:
        """Returns observer state"""

        if self._observer:
            return self._observer.is_alive()
        # else:
        logging.warning("Observer is no longer present")
        return False

    # 10 Set listener prop
    def set_listener(self, listener):
        """listener setter"""
        self.listener = listener

    def save(self):
        """Save model and folluw up"""

        self.model.save()
        if self._filedeleter.days != int(self.model.number_of_days):
            # Create new instance with new settings and start it
            self._filedeleter = FileDeleter(
                self.model.source_dir, int(self.model.number_of_days)
            )
            self.create_delete_thread()

        # 11 If monitoring is active ask the user if he wants to restart
        if self.is_monitoring():
            if messagebox.askyesno(
                title="sbRenamer",
                message="Restart listener to use new settings?",
            ):
                self.stop_monitoring()
                self.start_monitoring()

    def update_view(self):
        """Update View"""
        self.setting_view.updateSaveBtn(self.model.dirty)

    def update_widget(self, value):
        """update log widget"""
        self.renamer_view.addLine(value)


class FileDeleter:
    """Object to check and delete files"""

    def __init__(self, folder, days):
        # folder is the name of the folder in which we have to perform the delete operation
        self.folder = folder

        # N is the number of days for which we have to check whether the file is older
        # than the specified days or not
        self.days = int(days)
        logging.debug(
            "Initialised new deleter for path %s and %d number of days",
            self.folder,
            self.days,
        )

    def list_files(self):
        """function list all de files in self.folder and remove"""

        if self.days == 0:
            logging.info("Configured for no deletions")
            return

        logging.info("Listing files to check for deletion")
        # loop to check all files one by one

        for file in os.listdir(self.folder):
            logging.debug("found %s", file)
            file_2_examine = os.path.join(self.folder, file)
            if os.path.isfile(file_2_examine):
                logging.debug("found %s to be a file", file_2_examine)
                if self.file_is_to_old(file_2_examine):
                    # remove file
                    os.remove(file_2_examine)
                    logging.info("Deleting : %s", file_2_examine)

    def file_is_to_old(self, filename):
        """Function returns true if file is to old, modified longer than self.days ago"""
        # temp variable to store path of the file

        # get the timestamp, when the file was modified
        timestamp_of_file_modified = os.path.getmtime(filename)
        # convert timestamp to datetime
        modification_date = datetime.datetime.fromtimestamp(timestamp_of_file_modified)
        # find the number of days when the file was modified
        number_of_days = (datetime.datetime.now() - modification_date).days
        logging.debug("File is %d    day old", number_of_days)
        return number_of_days > self.days


class TimedList(list):
    """Custom implementation of a list that removes items after a fixed delay"""

    def __init__(self, ttl):
        self.list = []
        self._ttl = ttl

    def __ttl_remove(self, list_item):
        """Method that should only be called internally to remove item with delay"""
        time.sleep(self._ttl)
        self.list.remove(list_item)
        logging.debug("Removing %s from list", list_item)

    def append(self, __object) -> None:
        self.list.append(__object)
        logging.debug("Added item %s", __object)
        remove_thread = threading.Thread(
            target=self.__ttl_remove,
            args=(__object,),
        )
        remove_thread.start()

    def __contains__(self, __key: object) -> bool:
        return __key in self.list

    def __iter__(self) -> Iterator:
        for list_item in self.list:
            yield list_item


class RenameXmlHandler(PatternMatchingEventHandler):
    """Handler to catch newly created files and rename them"""

    # Set filename pattern
    # Mod 15
    patterns = ["*.xml", "*.fms"]
    DELAY_EXECUTION = 2
    CACHE_TTL = 3
    # Initialise fileNamesCreated, will be used to ignore the files created
    file_names_to_ignore = TimedList(CACHE_TTL)

    # 10 Added listener on construct
    def __init__(self, model: RenamerSettings, listener):
        PatternMatchingEventHandler.__init__(self)
        self.model = model
        self.listener = listener

    def execute_with_delay(self, method_to_execute, *args):
        """Default wrapper for delayed execution"""
        threading.Timer(self.DELAY_EXECUTION, method_to_execute, args=args).start()

    def on_modified(self, event):
        logging.info("Trigger modified file: %s", (event.src_path))

        newfile_path = pathlib.Path(event.src_path)
        newfile_stem = newfile_path.stem

        # Mod 15 rewrite of ignoring earlier created files
        if (newfile_path.name in self.file_names_to_ignore) and (
            "(1)" not in newfile_stem
        ):
            logging.debug(
                "Ignoring the %s (created or processed already)", newfile_stem
            )
            return

        self.file_names_to_ignore.append(newfile_path.name)
        # Mod 15 Check for extention
        if pathlib.Path(event.src_path).suffix == ".xml":
            if self.model.save_xml:
                self.execute_with_delay(
                    self.copy_shortend, event, self.model.new_filename(newfile_stem)
                )
            else:
                self.execute_with_delay(
                    self.rename_shortend, event, self.model.new_filename(newfile_stem)
                )

        else:
            # mod 15 This is a fms file
            if self.model.fms_format == self.model.FMS_BOTH:
                self.execute_with_delay(
                    self.copy_shortend, event, self.model.fms_filename()
                )

            elif self.model.fms_format == self.model.FMS_B738:
                self.execute_with_delay(
                    self.rename_shortend, event, self.model.fms_filename()
                )

    def copy_shortend(self, event, target_filename):
        """copy based on event source path"""

        logging.debug("Start copy target %s", target_filename)
        newfile_path = pathlib.Path(event.src_path)
        filename = newfile_path.stem
        # 10 Change destFile into Path, to use pathib functions
        dest_file = pathlib.Path(newfile_path.parent / target_filename)

        # mod 16
        if self.destination_equals_source(dest_file, newfile_path):
            return

        self.file_names_to_ignore.append(dest_file.name)
        if self.model.save_existing_target and dest_file.is_file():
            logging.info("Destination file exits")
            self.rename_existing_file(dest_file)

        try:
            shutil.copyfile(newfile_path, dest_file)
            logging.info("filename: %s copied to %s", filename, dest_file.name)
            # 10 If the listener is assigned, activate it with correct message
            if self.listener:
                self.listener(
                    f"filename: {filename} copied to {dest_file.name}",
                    "sbRenamer",
                )

        except shutil.Error as err:
            logging.error(
                "Unable to copy %s to %s, error: %s", filename, dest_file, err
            )

    # Mod 16
    def destination_equals_source(self, dest_file, source_file):
        """Check if files are the same (and existing)"""
        logging.debug("check if equal")
        if dest_file.is_file():
            return_value = dest_file.name == source_file.name
        else:
            return_value = False
        logging.debug("Equal check returns %s", return_value)
        return return_value

    def rename_shortend(self, event, target_filename):
        """Handle file created event by renaming the file that was created"""
        # This method needs to move to the Renamer model??
        logging.debug("Start rename")
        new_file_path = pathlib.Path(event.src_path)
        filename = new_file_path.stem
        # 10 Change destFile into Path, to use pathib functions
        dest_file = pathlib.Path(new_file_path.parent / target_filename)

        # Mod 16
        if self.destination_equals_source(dest_file, new_file_path):
            return

        # keep the new file to be created to check new event
        self.file_names_to_ignore.append(dest_file.name)
        if dest_file.is_file():
            self.handle_existing_destination(dest_file)

        try:
            new_file_path.rename(dest_file)
            logging.info("filename: %s renamed to %s", filename, dest_file.name)
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

    def handle_existing_destination(self, dest_file):
        """Removes or renames exisiting file"""
        logging.debug("Destination file exits")
        if self.model.save_existing_target:
            logging.debug("Renaming Existing Destination")
            self.rename_existing_file(dest_file)
        else:
            logging.debug("Removing Existing Destination")
            os.remove(dest_file)

    def rename_existing_file(self, file_to_rename):
        """renames file to samename with datetime"""

        logging.debug("Renaming file to datetime version")
        backup_file = file_to_rename.parent / pathlib.Path(
            file_to_rename.stem
            + "_"
            + time.strftime("%Y%m%d%H%M%S")
            + file_to_rename.suffix
        )
        try:
            self.file_names_to_ignore.append(backup_file.name)
            file_to_rename.rename(backup_file)
        except OSError as error:
            logging.error("problem with renaming existing file")
            logging.error(error)
            sys.exit(1)
        logging.info("Renamed existing file to %s", backup_file.name)


class MainApp(tk.Tk):
    """Main tk window"""

    def __init__(self):
        super().__init__()
        self.geometry("620x600")
        self.resizable(width=False, height=False)

        self.title("SimBrief Renamer by ChezHJ")
        self.iconbitmap("./sbRenamer.ico")
        # if we want parent frames to resize to there master, we need to update the app
        self.update()

        self._settings = SettingView(self)
        self._settings.grid(column=0, row=0, padx=5, pady=5, ipadx=5)

        self._renamer_view = RenamerView(self)
        self._renamer_view.grid(column=0, row=1, padx=5, pady=5, ipadx=5)

        self._config = RenamerSettings(CONFIGFILENAME)
        controller = Controller(self._config, self._settings, self._renamer_view)

        # should move to controller?
        self._settings.set_widgets(
            self._config.source_dir,
            self._config.file_format,
            self._config.FILEFORMATS,
            self._config.auto_start,
            self._config.auto_hide,
            self._config.fms_format,
            self._config.FMS_OPTIONS,
        )
        self._settings.set_delete_widgets(
            self._config.save_xml, self._config.number_of_days
        )

        self._settings.setLogWidgets(
            self._config.log_level, self._config.LOGLEVELS, self._config.log_to_file
        )

        self._controller = controller
        self._settings.set_controller(controller)
        self._renamer_view.set_controller(controller)

        self.bind("<Unmap>", self._resize_handler)

        self.hidden = False
        self.icon = None
        logging.info("Succesfully initialised version %s", __version__)

    def _resize_handler(self, event):
        minimize_event = False
        for key in dir(event):
            if not key.startswith("_"):
                saved_attr = getattr(event, key)

                if key == "widget" and isinstance(saved_attr, tk.Tk):
                    if getattr(event, "type") == "18":
                        minimize_event = True
        if minimize_event:
            self.hide_window()

    def hide_window_exit(self):
        """Hides self"""
        self.hide_window()

    def hide_window(self):
        """Hide to systray"""
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
        self._controller.set_listener(self.icon.notify)
        # Fixing issue 7, by starting the icon in a separate thread, not blocking other actions
        # Used to be self.icon.run()
        # Mod 13
        threading.Thread(daemon=True, target=self.icon.run).start()

        return

    def show_window(self):
        """Unhide from systray"""
        self.icon.stop()
        self.hidden = False
        self.deiconify()

    def close(self):
        """Safe close, stop monitoring first"""
        if self._controller.is_active_monitoring():
            logging.info("Stopping monitoring first")
            self._controller.stop_monitoring()
        self.destroy()

    def quit_window(self):
        """Quit function for icon menu"""
        self.icon.stop()
        self.close()


if __name__ == "__main__":
    try:
        app = MainApp()
    except FileNotFoundError as e:
        showerror("Error", e.filename + "\n" + e.strerror)
        sys.exit(1)

    app.mainloop()
