import inspect
import collections
from bytecode import Instr, Bytecode
from enum import Enum
from contextlib import redirect_stdout, redirect_stderr
import core.debuggerLoader as debuggerLoader
import sys


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
current_stacktrace = None


def debug():
    global current_program_frame, current_debugger_state, current_stacktrace
    current_stacktrace = get_stacktrace()
    current_program_frame = inspect.currentframe().f_back
    if current_debug_mode == DebugMode.StepMode or should_stop_on_breakpoint():
        current_debugger_state = DebuggerState.Stopped
    while current_debugger_state == DebuggerState.Stopped:
        current_debug_interface()


#  TESTS
def get_stacktrace():
    stack = collections.deque()
    current_frame = inspect.currentframe().f_back
    stack.appendleft(current_frame)
    while current_frame.f_back is not None:
        current_frame = current_frame.f_back
        stack.appendleft(current_frame)
    return stack


#  TESTS
def should_stop_on_breakpoint():
    line_num = get_line_number()
    filename = get_filename()
    if line_num in breakpoints and filename in breakpoints[line_num]:
        if breakpoints[line_num][filename] is not None:
            try:
                return eval(breakpoints[line_num][filename].condition, *get_globals_and_locals())
            except Exception:
                raise Exception  # What type of exception should I use?
        return True
    return False


def get_code_context():
    __, line_number, __, lines, __ = inspect.getframeinfo(
        current_program_frame, 100000)  # I don't know how to force this func to return all lines
    return lines, line_number


def get_globals_and_locals():
    return current_program_frame.f_globals, current_program_frame.f_locals


def set_debug_mode(new_mode):
    global current_debug_mode
    current_debug_mode = DebugMode(new_mode)


def get_debug_mode():
    return current_debug_mode


#   TESTS
def add_breakpoint(filename, line_number, condition=None):
    if line_number not in breakpoints:
        breakpoints[line_number] = dict()
    if filename in breakpoints[line_number]:
        raise LookupError
    breakpoints[line_number][filename] = Breakpoint(filename, line_number, condition)


#   TESTS
def remove_breakpoint(filename, line_number):
    if line_number in breakpoints and filename in breakpoints[line_number]:
        del breakpoints[line_number][filename]
    else:
        raise LookupError


def get_all_breakpoints():
    return breakpoints


def get_line_number():
    return current_program_frame.f_lineno


def get_filename():
    (filename, _, _, _, _) = inspect.getframeinfo(current_program_frame)
    return filename


# TESTS
def modify_var(out_depth, modify_expression):
    dicts = (current_stacktrace[out_depth].f_globals, current_stacktrace[out_depth].f_locals)
    exec_code(modify_expression, dicts)


# TESTS
def exec_code(code, dicts=None):
    if dicts is None:
        dicts = get_globals_and_locals()
    compiled_code = compile(code, "Debug Code", 'exec')
    try:
        exec(compiled_code, *dicts)
    except Exception:
        raise Exception  # What type of Exception should I use?


def modify_code(file_code):
    file_bytecode = Bytecode.from_code(file_code)
    current_line = -1
    modified_bytecode = []
    for instruction in file_bytecode:
        if hasattr(instruction, "lineno"):
            if current_line != instruction.lineno:
                current_line = instruction.lineno
                modified_bytecode.append(
                    Instr('LOAD_GLOBAL', 'debug',
                          lineno=current_line), )
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
    debuggerLoader.install_custom_loader(debug)
    with open(file, 'r', encoding='utf8') as code:
        compiled_code = compile(code.read(), file, 'exec')
        modified_code = modify_code(compiled_code)
    _globals = {
        'debug': debug,
        '__name__': '__main__',
    }
    with redirect_stdout(sys.stdout), redirect_stderr(sys.stderr):
        exec(modified_code, _globals)
