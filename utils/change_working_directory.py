from contextlib import AbstractContextManager
import os


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
