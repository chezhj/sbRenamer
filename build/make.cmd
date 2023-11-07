@echo off
pyinstaller --noconfirm --onedir --windowed --icon "C:/Code/sbRenamer/sbRenamer.ico" --clean --add-data "C:/Code/sbRenamer/sbRenamer.ico;."  "C:/Code/sbRenamer/sbRenamer.py" --distpath "C:/Code/sbRenamer/output" --workpath C:\Users\hvdwa\AppData\Local\Temp\build --specpath C:\Users\hvdwa\AppData\Local\Temp\spec

