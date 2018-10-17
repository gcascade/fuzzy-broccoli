# fuzzy-broccoli
How to install

Step 1 - Install Python 3.6. Do not install 3.7 it is not compatible with cx_Freeze for now (15-Oct-2018)
https://www.python.org/downloads/
You can add Python to path

Step 2 - Install cx_Freeze, Pygame and lxml
Execute pip install cx_Freeze on a prompt
if it does not work, check cx_Freeze's website : https://cx-freeze.readthedocs.io/en/latest/
pip install pygame
pip install lxml

Step 3 - Create .Exe file
Open a prompt in the game's directory
python setup.py build

Step 4 - Copy the following folders in the build\exe.win-amd64-3.6 directory
Abitilies
Data
Levels
Utilities
