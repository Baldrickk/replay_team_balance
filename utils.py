"""TODO: Module Docstring"""
import sys

class OverWriter:
    """TODO: Class Docstring"""
    def __init__(self, output=sys.stderr):
        """TODO: Method Docstring"""
        self.length = 0
        self.output = output

    def __enter__(self):
        """TODO: Method Docstring"""
        return self

    def __exit__(self, type, value, traceback):
        """TODO: Method Docstring"""
        self.close()

    def print(self, print_string):
        """TODO: Method Docstring"""
        self.length = max(self.length, len(print_string))
        print('\r' + print_string.ljust(self.length), end='', file=self.output, flush=True)

    @staticmethod
    def close():
        """TODO: Method Docstring"""
        print('\n')
