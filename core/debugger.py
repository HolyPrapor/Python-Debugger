#!/usr/bin/env python3

import inspect
from bytecode import Instr, Bytecode
from enum import Enum


class Breakpoint:
    def __init__(self, filename, line_number, condition=None):
        self.filename = filename
        self.line_number = line_number
        self.condition = condition

    def __eq__(self, other):
        return (self.filename, self.line_number, self.condition) == \
               (other.filename, other.line_number, other.condition)


class DebugMode(Enum):
    StepMode = 1
    BreakpointMode = 2


class DebuggerState(Enum):
    Running = 1
    Stopped = 2


current_debugger_state = DebuggerState.Stopped
current_debug_mode = DebugMode.StepMode
breakpoints = dict()
current_debug_interface = None
current_program_frame = None


def debug():
    global current_program_frame, current_debugger_state
    current_program_frame = inspect.currentframe().f_back
    if current_debug_mode == DebugMode.StepMode or \
            get_line_number() in breakpoints:
        current_debugger_state = DebuggerState.Stopped
    while current_debugger_state == DebuggerState.Stopped:
        current_debug_interface()


def get_code_context():
    __, line_number, __, lines, __ = inspect.getframeinfo(
        current_program_frame, 10)
    return lines, line_number


def get_globals_and_locals():
    return current_program_frame.f_globals, current_program_frame.f_locals


def set_debug_mode(new_mode):
    global current_debug_mode
    current_debug_mode = DebugMode(new_mode)


def get_debug_mode():
    return current_debug_mode


def add_breakpoint(filename, line_number, condition=None):
    if line_number in breakpoints:
        breakpoints[line_number].append(
            Breakpoint(filename, line_number, condition))
    else:
        breakpoints[line_number] = [Breakpoint(
            filename, line_number, condition)]


def remove_breakpoint(filename, line_number, condition=None):
    # breakpoints[line_number].remove(
    # Breakpoint(filename, line_number, condition))
    del breakpoints[line_number]


def get_all_breakpoints():
    return breakpoints


def get_line_number():
    return current_program_frame.f_lineno


def modify_code(file_code):
    file_bytecode = Bytecode.from_code(file_code)
    current_line = -1
    modified_bytecode = []
    for instruction in file_bytecode:
        if current_line != instruction.lineno:
            current_line = instruction.lineno
            modified_bytecode.append(
                Instr('LOAD_GLOBAL', 'debug',
                      lineno=current_line))
            modified_bytecode.append(
                Instr('CALL_FUNCTION', 0,
                      lineno=current_line))
            modified_bytecode.append(
                Instr('POP_TOP',
                      lineno=current_line))
        if instruction.name == "LOAD_CONST" \
                and type(instruction.arg) == type(file_code):
            modified_bytecode.append(
                Instr('LOAD_CONST',
                      modify_code(instruction.arg),
                      lineno=current_line))
        else:
            modified_bytecode.append(instruction)
    file_bytecode.clear()
    for instruction in modified_bytecode:
        file_bytecode.append(instruction)
    return file_bytecode.to_code()


def continue_until_breakpoint():
    global current_debugger_state, current_debug_mode
    current_debug_mode = DebugMode.BreakpointMode
    current_debugger_state = DebuggerState.Running


def make_step():
    global current_debugger_state, current_debug_mode
    current_debugger_state = DebuggerState.Running
    current_debug_mode = DebugMode.StepMode


def start_debugging(debug_function, file, mode=DebugMode.StepMode):
    global current_debug_interface, current_debug_mode
    current_debug_interface = debug_function
    current_debug_mode = DebugMode(mode)
    with open(file, 'r') as code:
        compiled_code = compile(code.read(), file, 'exec')
        modified_code = modify_code(compiled_code)
    _globals = {
        'debug': debug,
        '__name__': '__main__',
    }
    exec(modified_code, _globals)
