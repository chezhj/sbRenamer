# sbRenamer

#Building the exe
auto-py-to-exe.exe -c .\auto2Exe.json    

pyinstaller --noconfirm --onedir --windowed --icon "C:/Code/sbRenamer/sbRenamer.ico" --clean --add-data "C:/Code/sbRenamer/sbRenamer.ico;."  "C:/Code/sbRenamer/sbRenamer.py"

C:\Code\sbRenamer> pyinstaller --noconfirm --onedir --windowed --icon "C:/Code/sbRenamer/sbRenamer.ico" --clean --add-data "C:/Code/sbRenamer/sbRenamer.ico;."  "C:/Code/sbRenamer/sbRenamer.py" --distpath "C:/Code/sbRenamer/output" --workpath C:\Users\hvdwa\AppData\Local\Temp\ --specpath C:\Users\hvdwa\AppData\Local\Temp\

pyinstaller --noconfirm --onedir --windowed --icon C:/Code/sbRenamer/sbRenamer.ico --clean --add-data C:/Code/sbRenamer/sbRenamer.ico;. C:/Code/sbRenamer/sbRenamer.py --distpath C:\Users\hvdwa\AppData\Local\Temp\tmpgkzmqo6f\application --workpath C:\Users\hvdwa\AppData\Local\Temp\tmpgkzmqo6f\build --specpath C:\Users\hvdwa\AppData\Local\Temp\tmpgkzmqo6f

Will have to use the prehook of commitizen to build new exe on bump


open sbRenamer.iss in InnoSetupCompiler
Check version
Build exe

 py -m coverage erase
 py -m coverage run -m unittest discover test/
 py -m coverage html 
 py -m coverage lcov -o cov.xml

#Correct ways to bump
cz bump  -pr beta --increment MAJOR
Does not have the exe so need to bump again

cz bump --files-only --yes --changelog
git commit -am "bump: release $(cz version --project)"

And later on to create the tag:

git tag $(cz version --project)

Commitizen works well with git, and where commitizen is available you know git will be available, this gives you a lot of flexibility.

Maybe we could add this as a tutorial? 🤔