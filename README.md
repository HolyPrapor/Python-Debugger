# Python Debugger
Version 1.0

Author: Tzoop Ilya (ilyatzoop@gmail.com)


## Description
Created as a part of university project. Used for debugging python programs.


## Requirements
* Installed "bytecode" module
* Installed "PyQT5" module
* Installed "qscintilla" module


## Structure
* Console version: `consoleDebugger.py`
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

* All information is located on the help page.


## Implementation details
This python debugger uses bytecode module to insert debug function on every line. In other words, we call debug control function before we execute the current line code. Then we use different python modules to get information about stacktrace, code context, etc...

Supports debugging from imported modules (custom import mechanic is used).

GUI uses PyQT5 as main engine, and Qscintilla for code editor widget.
