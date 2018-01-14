import sys


class OverWriter:
    def __init__(self, output=sys.stdout):
        self.length = 0
        self.output = output

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.close()

    def _print(self, print_string, start_char):
        if len(print_string) > self.length:
            self.length = len(print_string)
        print(start_char + print_string.ljust(self.length), end='', file=self.output, flush=True)

    def print_over(self, print_string):
        self._print(print_string, '\r')

    def print_line(self, print_string):
        self._print(print_string, '\n')

    @staticmethod
    def close():
        print('\n')
