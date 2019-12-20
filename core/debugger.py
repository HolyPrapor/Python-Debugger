import inspect
import collections
from bytecode import Instr, Bytecode
from enum import Enum
from contextlib import redirect_stdout, redirect_stderr
import core.debuggerLoader as debuggerLoader
import sys
import traceback


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
        self.step_over_filename = None
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
        if self.current_debugger_state == DebuggerState.Stopped:
            self.current_debug_interface()
        while self.current_debugger_state == DebuggerState.Stopped:
            pass

    def get_stacktrace(self):
        stack = collections.deque()
        current_frame = inspect.currentframe().f_back.f_back
        stack.append(current_frame)
        while current_frame.f_back is not None:
            current_frame = current_frame.f_back
            stack.append(current_frame)
        return stack

    def should_stop_on_breakpoint(self):
        line_num = self.get_line_number()
        filename = self.get_filename()
        if self.step_over_filename == filename:
            self.step_over_filename = None
            return True
        if line_num in self.breakpoints and\
                filename in self.breakpoints[line_num]:
            if self.breakpoints[line_num][filename].condition is not None:
                try:
                    return eval(self.breakpoints[line_num][filename].condition,
                                *self.get_globals_and_locals())
                except:
                    print("Condition was wrong. Stopping.", file=sys.stderr)
                    return True
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
        # else:
        #    raise LookupError

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
        except:
            print("Exception caught", file=sys.stderr)
            print(sys.exc_info(), file=sys.stderr)

    def continue_until_breakpoint(self):
        self.current_debug_mode = DebugMode.BreakpointMode
        self.current_debugger_state = DebuggerState.Running

    def make_step(self):
        self.current_debugger_state = DebuggerState.Running
        self.current_debug_mode = DebugMode.StepMode

    def step_over(self):
        self.step_over_filename = self.get_filename()
        self.current_debug_mode = DebugMode.BreakpointMode
        self.current_debugger_state = DebuggerState.Running

    def start_debugging(self, debug_function, file, mode=DebugMode.StepMode,
                        stdout=sys.stdout, stderr=sys.stderr,
                        stdin=sys.stdin,
                        after_debug_func=None):
        self.current_debug_interface = debug_function
        self.current_debug_mode = DebugMode(mode)
        debuggerLoader.install_custom_loader(self.debug)
        with open(file, 'r') as code:
            compiled_code = compile(code.read(), file, 'exec')
            modified_code = modify_code(compiled_code)
        _globals = {
            'debug': self.debug,
            '__name__': '__main__',
        }
        with redirect_stdout(stdout), redirect_stderr(stderr):
            sys.stdin = stdin
            try:
                exec(modified_code, _globals)
            except:
                traceback.print_exc(file=sys.stderr)
            if after_debug_func:
                after_debug_func()
        debuggerLoader.remove_custom_loader_and_invalidate_caches()


def modify_code(file_code):
    file_bytecode = Bytecode.from_code(file_code)
    modified_lines = []
    modified_bytecode = []
    for instruction in file_bytecode:
        if hasattr(instruction, "lineno"):
            if instruction.lineno not in modified_lines:
                modified_lines.append(instruction.lineno)
                modified_bytecode.append(
                    Instr('LOAD_GLOBAL', 'debug',
                          lineno=instruction.lineno), )
                modified_bytecode.append(
                    Instr('CALL_FUNCTION', 0,
                          lineno=instruction.lineno))
                modified_bytecode.append(
                    Instr('POP_TOP',
                          lineno=instruction.lineno))
            if instruction.name == "LOAD_CONST" \
                    and type(instruction.arg) == type(file_code) \
                    and is_source_available(instruction.arg):
                modified_bytecode.append(
                    Instr('LOAD_CONST',
                          modify_code(instruction.arg),
                          lineno=instruction.lineno))
            else:
                modified_bytecode.append(instruction)
        else:
            modified_bytecode.append(instruction)
    file_bytecode.clear()
    for instruction in modified_bytecode:
        file_bytecode.append(instruction)
    return file_bytecode.to_code()


def is_source_available(function):
    try:
        inspect.getsource(function)
        return True
    except OSError:
        return False
