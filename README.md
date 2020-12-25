# Python Debugger
Version 1.0

Author: Tzoop Ilya (tolya12345w@gmail.com)


## Description
This application was created for debugging python programs.


## Requirements
* Installed "bytecode" module
* Installed "PyQT5" module
* Installed "qscintilla" module


## Structure
* Console version: `consoleDebugger.py` # NOT RECOMMENDED TO USE
* GUI version: `guiDebugger.py`


## Console version
Help: `./consoleDebugger.py --help`

Launch example: `./consoleDebugger.py testProgramsToDebug/calculate.py`

### Usage

* `command list` — Show list of commands
* `Number of command "COMMAND" in command list` — Launch "COMMAND"

## GUI version
Help: Ctrl + I 

### Usage

* All information located on the help page.


## Implementation details
This python debugger uses bytecode module to insert debug fuction on every line. This means, that on each line your debug function is executed. Then we use different python modules to get information about stacktrace, code context, current line. 
Import modules works through custom import module. Additional information can be gathered in source files.

GUI uses PyQT5 as main engine, and Qscintilla for code editor widget.
