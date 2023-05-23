# sbRenamer

#Building the exe
auto-py-to-exe.exe -c .\auto2Exe.json    

open sbRenamer.iss in InnoSetupCompiler
Check version
Build exe

 py -m coverage erase
 py -m coverage run -m unittest discover test/
 py -m coverage html 
