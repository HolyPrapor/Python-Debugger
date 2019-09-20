#!/usr/bin/env python3

import core.debugger as debugger
import os
import argparse


def print_debug_commands():
    """Command list
    Prints list of all commands"""
    for index, command in enumerate(commands):
        print(str(index + 1) + ". " + command.__doc__)


def make_step():
    """Make step
    Program continues to next line"""
    debugger.make_step()


def continue_until_breakpoint():
    """Continue
    Continues until next breakpoint or end of program"""
    debugger.continue_until_breakpoint()


def show_context():
    """Show context
    Shows current frame context"""
    context, current_line = debugger.get_code_context()
    context[current_line - 1] = context[current_line - 1].rstrip() \
                                + "   < ----- Current line"
    for line in context:
        print(line)


def show_variables():
    """Show variables
    Shows globals and locals"""
    global_dict, local_dict = debugger.get_globals_and_locals()
    print("GLOBALS:")
    for global_var in global_dict:
        if global_var == "__builtins__" or global_var == "debug":
            continue
        print("  " + str(global_var) + " = " + str(global_dict[global_var]))
    if global_dict != local_dict:
        print("LOCALS:")
        for local_var in local_dict:
            if local_var == "__builtins__" or local_var == "debug":
                continue
            print("  " + str(local_var) + " = " + str(local_dict[local_var]))


def set_debug_mode():
    """Set debug mode
    Sets debug mode"""
    print("Setting debug mode...")
    debugger.set_debug_mode(int(input(
        "1. StepMode\n2. BreakpointMode\nMode(numeric): ")))


def get_debug_mode():
    """Get debug mode
    Gets debug mode"""
    print(debugger.get_debug_mode())


def add_breakpoint():
    """Add breakpoint
    Adds breakpoint"""
    print("Adding breakpoint...")
    debugger.add_breakpoint(input("Filename: "), int(input("Line number: ")))


def remove_breakpoint():
    """Remove breakpoint
    Removes breakpoint"""
    print("Removing breakpoint...")
    debugger.remove_breakpoint(
        input("Filename: "), int(input("Line number: ")))


def print_breakpoint_list():
    """Breakpoint list
    Prints list of all breakpoints"""
    print(debugger.get_all_breakpoints())


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def debug():
    command = input("Command: ").casefold()
    clear_console()
    if command == "command list":
        print_debug_commands()
    elif command == "make step":
        make_step()
    elif command == "continue":
        continue_until_breakpoint()
    elif command == "show context":
        show_context()
    elif command == "show variables":
        show_variables()
    elif command == "set debug mode":
        set_debug_mode()
    elif command == "get debug mode":
        get_debug_mode()
    elif command == "add breakpoint":
        add_breakpoint()
    elif command == "remove breakpoint":
        remove_breakpoint()
    elif command == "breakpoint list":
        print_breakpoint_list()
    elif command.isnumeric():
        commands[int(command) - 1]()
    else:
        print("No command found! Try again!")


def parse_args():
    """Argparse setup"""
    parser = argparse.ArgumentParser(
        description='Utility for debugging python files.')
    file_to_debug = parser.add_argument('file', help='File to debug')
    file_to_debug.required = True
    debugging_mode = parser.add_argument('--mode',
                                         type=int,
                                         help='Debugging mode\n'
                                              '1. StepMode\n'
                                              '2. BreakpointMode\n'
                                              'Default = StepMode',
                                         default=debugger.DebugMode.StepMode)
    return parser.parse_args()


commands = (print_debug_commands, make_step, continue_until_breakpoint,
            show_context, show_variables,
            set_debug_mode, get_debug_mode, add_breakpoint,
            remove_breakpoint, print_breakpoint_list)


def main():
    args = parse_args()
    print("Welcome to Python Debugger!")
    print("Print 'Command list' to get list of available commands.")
    debugger.start_debugging(debug, args.file, args.mode)


if __name__ == '__main__':
    main()
