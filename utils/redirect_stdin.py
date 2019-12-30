from contextlib import AbstractContextManager
import sys


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
