#!/usr/bin/env python3

import unittest
import os
import sys
import importlib

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))

import core.debugger as debugger
from utils.tempfiles import TempFiles

sys_path_hooks_init_len = len(sys.path_hooks)


def print_lines_to_file(lines, filename):
    with open(filename, 'w', encoding='utf8') as f:
        for line in lines:
            print(line, file=f)


class DebuggerTests(unittest.TestCase):
    def tearDown(self):
        if len(sys.path_hooks) > sys_path_hooks_init_len:
            del sys.path_hooks[0]
            importlib.reload(debugger)

    def test_breakpoint_non_conditional_breakpoint_stops_where_expected(self):
        current_program_state = 0
        with TempFiles(1) as tempfiles:
            print_lines_to_file(['a = 0',
                                 'b = 1',
                                 'c = 2',
                                 'd = 3'], tempfiles[0].name)

            def machine():
                nonlocal current_program_state
                current_program_state += 1
                if current_program_state == 1:
                    debugger.add_breakpoint(tempfiles[0].name, 2)
                    debugger.continue_until_breakpoint()
                elif current_program_state == 2:
                    self.assertEqual(debugger.get_line_number(), 2)
                    debugger.add_breakpoint(tempfiles[0].name, 4)
                    debugger.continue_until_breakpoint()
                elif current_program_state == 3:
                    self.assertEqual(debugger.get_line_number(), 4)
                    debugger.continue_until_breakpoint()

            debugger.start_debugging(machine, tempfiles[0].name,
                                     debugger.DebugMode.StepMode)

    def test_breakpoint_remove_works_correctly(self):
        current_program_state = 0
        with TempFiles(1) as tempfiles:
            print_lines_to_file(['a = 0',
                                 'b = 1',
                                 'c = 2',
                                 'd = 3'], tempfiles[0].name)

            def machine():
                nonlocal current_program_state
                current_program_state += 1
                if current_program_state == 1:
                    debugger.add_breakpoint(tempfiles[0].name, 2)
                    debugger.add_breakpoint(tempfiles[0].name, 4)
                    debugger.remove_breakpoint(tempfiles[0].name, 2)
                    debugger.continue_until_breakpoint()
                elif current_program_state == 2:
                    self.assertEqual(debugger.get_line_number(), 4)
                    debugger.continue_until_breakpoint()

            debugger.start_debugging(machine, tempfiles[0].name,
                                     debugger.DebugMode.StepMode)

    def test_conditional_breakpoint_stops_where_expected(self):
        current_program_state = 0
        with TempFiles(1) as tempfiles:
            print_lines_to_file(['a = 0',
                                 'b = 1',
                                 'c = 2',
                                 'd = 3'], tempfiles[0].name)

            def machine():
                nonlocal current_program_state
                current_program_state += 1
                if current_program_state == 1:
                    debugger.add_breakpoint(tempfiles[0].name, 2, 'a == 1')
                    debugger.add_breakpoint(tempfiles[0].name, 4)
                    debugger.continue_until_breakpoint()
                elif current_program_state == 2:
                    self.assertEqual(debugger.get_line_number(), 4)
                    debugger.continue_until_breakpoint()

            debugger.start_debugging(machine, tempfiles[0].name,
                                     debugger.DebugMode.StepMode)

    def test_should_stop_on_breakpoint_returns_correct_value(self):
        current_program_state = 0
        with TempFiles(1) as tempfiles:
            print_lines_to_file(['a = 0',
                                 'b = 1',
                                 'c = 2',
                                 'd = 3'], tempfiles[0].name)

            debugger.add_breakpoint(tempfiles[0].name, 1)

            def machine():
                nonlocal current_program_state
                current_program_state += 1
                if current_program_state == 1:
                    self.assertTrue(debugger.should_stop_on_breakpoint())
                    debugger.add_breakpoint(tempfiles[0].name, 2)
                    debugger.continue_until_breakpoint()
                elif current_program_state == 2:
                    self.assertTrue(debugger.should_stop_on_breakpoint())
                    debugger.continue_until_breakpoint()

            debugger.start_debugging(machine, tempfiles[0].name,
                                     debugger.DebugMode.StepMode)

    def test_get_globals_and_locals_returns_correct_dictionaries(self):
        current_program_state = 0
        with TempFiles(1) as tempfiles:
            print_lines_to_file(['a = 0',
                                 'b = 1',
                                 'c = 2',
                                 'd = 3'], tempfiles[0].name)

            def machine():
                nonlocal current_program_state
                current_program_state += 1
                if current_program_state == 1:
                    _globals, _locals = debugger.get_globals_and_locals()
                    for i in range(4):
                        self.assertFalse(i in _globals.values())
                        self.assertFalse(i in _locals.values())
                    debugger.add_breakpoint(tempfiles[0].name, 4)
                    debugger.continue_until_breakpoint()
                elif current_program_state == 2:
                    _globals, _locals = debugger.get_globals_and_locals()
                    for i in range(3):
                        self.assertTrue(i in _globals.values())
                        self.assertTrue(i in _locals.values())
                    self.assertFalse(4 in _globals.values())
                    self.assertFalse(4 in _locals.values())
                    for letter in ['a', 'b', 'c']:
                        self.assertTrue(letter in _globals.keys())
                        self.assertTrue(letter in _locals.keys())
                    self.assertFalse('d' in _globals.keys())
                    self.assertFalse('d' in _locals.keys())
                    debugger.continue_until_breakpoint()

            debugger.start_debugging(machine, tempfiles[0].name,
                                     debugger.DebugMode.StepMode)

    def test_modify_var_works_correctly(self):
        current_program_state = 0
        with TempFiles(1) as tempfiles:
            print_lines_to_file(['a = 0',
                                 'b = 1',
                                 'c = 2',
                                 'd = 3'], tempfiles[0].name)

            def machine():
                nonlocal current_program_state
                current_program_state += 1
                if current_program_state == 1:
                    debugger.add_breakpoint(tempfiles[0].name, 3)
                    debugger.continue_until_breakpoint()
                elif current_program_state == 2:
                    debugger.add_breakpoint(tempfiles[0].name, 4)
                    debugger.modify_var(1, 'b = 0.02')  # 1 - because we are
                    # in test
                    debugger.continue_until_breakpoint()
                elif current_program_state == 3:
                    _globals, _locals = debugger.get_globals_and_locals()
                    self.assertEqual(_locals['b'], 0.02)
                    debugger.continue_until_breakpoint()

            debugger.start_debugging(machine, tempfiles[0].name,
                                     debugger.DebugMode.StepMode)

    def test_exec_code_works_correctly(self):
        current_program_state = 0
        with TempFiles(1) as tempfiles:
            print_lines_to_file(['def test_func(value): global a; a = value',
                                 'a = 0',
                                 'b = 1',
                                 'c = 2',
                                 'd = 3'], tempfiles[0].name)

            def machine():
                nonlocal current_program_state
                current_program_state += 1
                if current_program_state == 1:
                    debugger.add_breakpoint(tempfiles[0].name, 4)
                elif current_program_state == 2:
                    debugger.exec_code('test_func(5)')
                    _globals, _locals = debugger.get_globals_and_locals()
                    self.assertEqual(_globals['a'], 5)
                debugger.continue_until_breakpoint()

            debugger.start_debugging(machine, tempfiles[0].name,
                                     debugger.DebugMode.StepMode)

    def test_imported_code_breakpoints(self):
        current_program_state = 0
        stopped = False

        with TempFiles(2) as tempfiles:
            test_filename = tempfiles[0].name
            imported_filename = tempfiles[1].name

            print_lines_to_file(['import sys',
                                 'sys.path.append({})'.format(
                                     repr(os.path.dirname(imported_filename))),
                                 'import {}'.format(
                                     os.path.splitext(
                                         os.path.basename(
                                             imported_filename))[0])],
                                test_filename)

            print_lines_to_file(['a = 1',
                                 'b = 2'], imported_filename)

            def machine():
                nonlocal current_program_state, stopped
                current_program_state += 1
                if current_program_state == 1:
                    debugger.add_breakpoint(imported_filename, 2)
                    debugger.continue_until_breakpoint()
                elif current_program_state == 2:
                    self.assertEqual(debugger.get_filename(),
                                     imported_filename)
                    stopped = True
                    debugger.continue_until_breakpoint()

            debugger.start_debugging(machine, test_filename,
                                     debugger.DebugMode.StepMode)
        self.assertTrue(stopped)
