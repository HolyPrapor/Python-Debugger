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


class Debugger:
    def __init__(self):
        self.current_debugger_state = DebuggerState.Stopped
        self.current_debug_mode = DebugMode.StepMode
        self.breakpoints = dict()
        self.current_debug_interface = None
        self.current_program_frame = None
        self.current_stacktrace = None

    def debug(self):
        self.current_stacktrace = self.get_stacktrace()
        self.current_program_frame = inspect.currentframe().f_back
        if self.current_debug_mode == DebugMode.StepMode or\
                self.should_stop_on_breakpoint():
            self.current_debugger_state = DebuggerState.Stopped
        while self.current_debugger_state == DebuggerState.Stopped:
            self.current_debug_interface()

    def get_stacktrace(self):
        stack = collections.deque()
        current_frame = self.current_program_frame
        stack.append(current_frame)
        while current_frame.f_back is not None:
            current_frame = current_frame.f_back
            stack.append(current_frame)
        return stack

    def should_stop_on_breakpoint(self):
        line_num = self.get_line_number()
        filename = self.get_filename()
        if line_num in self.breakpoints and\
                filename in self.breakpoints[line_num]:
            if self.breakpoints[line_num][filename].condition is not None:
                try:
                    return eval(self.breakpoints[line_num][filename].condition,
                                *self.get_globals_and_locals())
                except Exception:
                    raise Exception  # What type of exception should I use?
            return True
        return False

    def get_code_context(self):
        __, line_number, __, lines, __ = inspect.getframeinfo(
            self.current_program_frame, 100000)  # I don't know how to
        # force this func to return all lines
        return lines, line_number

    def get_globals_and_locals(self):
        return (self.current_program_frame.f_globals,
                self.current_program_frame.f_locals)

    def set_debug_mode(self, new_mode):
        self.current_debug_mode = DebugMode(new_mode)

    def get_debug_mode(self):
        return self.current_debug_mode

    def add_breakpoint(self, filename, line_number, condition=None):
        if line_number not in self.breakpoints:
            self.breakpoints[line_number] = dict()
        if filename in self.breakpoints[line_number]:
            raise LookupError
        self.breakpoints[line_number][filename] = \
            Breakpoint(filename, line_number, condition)

    def remove_breakpoint(self, filename, line_number):
        if line_number in self.breakpoints and\
                filename in self.breakpoints[line_number]:
            del self.breakpoints[line_number][filename]
        else:
            raise LookupError

    def get_all_breakpoints(self):
        return self.breakpoints

    def get_line_number(self):
        return self.current_program_frame.f_lineno

    def get_filename(self):
        (filename, _, _, _, _) = \
            inspect.getframeinfo(self.current_program_frame)
        return filename

    def modify_var(self, out_depth, modify_expression):
        dicts = (self.current_stacktrace[out_depth].f_globals,
                 self.current_stacktrace[out_depth].f_locals)
        self.exec_code(modify_expression, dicts)

    def exec_code(self, code, dicts=None):
        if dicts is None:
            dicts = self.get_globals_and_locals()
        compiled_code = compile(code, "Debug Code", 'exec')
        try:
            exec(compiled_code, *dicts)
        except Exception:
            raise Exception  # What type of Exception should I use?

    def continue_until_breakpoint(self):
        self.current_debug_mode = DebugMode.BreakpointMode
        self.current_debugger_state = DebuggerState.Running

    def make_step(self):
        self.current_debugger_state = DebuggerState.Running
        self.current_debug_mode = DebugMode.StepMode

    def start_debugging(self, debug_function, file, mode=DebugMode.StepMode):
        self.current_debug_interface = debug_function
        self.current_debug_mode = DebugMode(mode)
        debuggerLoader.install_custom_loader(self.debug)
        with open(file, 'r', encoding='utf8') as code:
            compiled_code = compile(code.read(), file, 'exec')
            modified_code = modify_code(compiled_code)
        _globals = {
            'debug': self.debug,
            '__name__': '__main__',
        }
        with redirect_stdout(sys.stdout), redirect_stderr(sys.stderr):
            exec(modified_code, _globals)


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
