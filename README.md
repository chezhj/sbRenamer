# sbRenamer

The goal of this project is two fold
1: learn how to do stuff in python
2: make something usefull

I fly in X-plane with the use of Simbrief. There is an expert utility, the simbrief downloader, 
that helps you download particular files for the flight planned
The ZIBO mod, a wonderfull Boeing 738 plane, can read flightplan and weather from the xml download
but it needs to have the same stem. 
So if you flightplan is EHAMLFPG.fpl the xml should also be EHAMLFPG.xml 
This tools monitors a diretory for xmlfiles newly created, then renames while saving any older files
