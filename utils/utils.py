from contextlib import AbstractContextManager
import sys
import os


class change_sys_arguments(AbstractContextManager):
    def __init__(self, new_arguments):
        self.new_arguments = new_arguments
        self.previous_arguments = None

    def __enter__(self):
        self.previous_arguments = sys.argv
        new_arguments = [os.getcwd(), *self.new_arguments]
        sys.argv = new_arguments
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.argv = self.previous_arguments


class change_working_directory(AbstractContextManager):
    def __init__(self, new_directory):
        self.new_directory = new_directory
        self.previous_directory = None

    def __enter__(self):
        self.previous_directory = os.getcwd()
        os.chdir(self.new_directory)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.previous_directory)


class redirect_stdin(AbstractContextManager):
    def __init__(self, new_input):
        self.new_input = new_input
        self.previous_input = None

    def __enter__(self):
        self.previous_input = sys.stdin
        sys.stdin = self.new_input
        return self.new_input

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdin = self.previous_input
