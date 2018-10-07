from cx_Freeze import setup, Executable

setup(
    name="Fuzzy-Broccoli",
    version="0.1",
    description="Fuzzy-Broccoli",
    executables=[Executable("main.py")],
    includes=['lxml.etree'],
)