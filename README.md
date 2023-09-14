# sbRenamer

Version 0.7.1
ALFA TESTING
Use at own risks

see https://github.com/chezhj/sbRenamer/wiki for installation and manual

The goal of this project is two fold
1: learn how to do stuff in python
2: make something usefull

I fly in X-plane with the use of Simbrief. There is an expert utility, the simbrief downloader, 
that helps you download particular files for the flight planned
The ZIBO mod, a wonderfull Boeing 738 plane, can read flightplan and weather from the xml download
but it needs to have the same stem. 
So if you flightplan is EHAMLFPG.fpl the xml should also be EHAMLFPG.xml 
This tools monitors a diretory for xmlfiles newly created, then renames while saving any older files

Installation use installer sbRenamerInstaller.exe


Thanks to 
* Ryan M Smith for python-watchdog.py from https://gist.github.com/rms1000watt
* Stephen Friederichs (https://github.com/sfriederichs) for logging  
   http://sfriederichs.github.io/how-to/python/gui/logging/2017/12/21/Python-GUI-Logging.html
* Dev Prakash Sharma (https://github.com/codewithdev ?) for the system tray info 
   https://www.tutorialspoint.com/how-to-make-a-system-tray-application-in-tkinter#


And websites
* https://www.pythontutorial.net/tkinter/tkinter-mvc/
