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
        print(new_arguments)
        for i in new_arguments:
            print(i)
        sys.argv = new_arguments
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.argv = self.previous_arguments
