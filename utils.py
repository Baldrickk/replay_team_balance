import sys

class one_line_string:
  def __init__(self, output=sys.stdout):
    self.length = 0
    self.output = output
  
  def print(self, print_string):
    if len(print_string) > self.length:
      self.length = len(print_string)
    print('\r' + print_string.ljust(self.length), 
          end = '', 
          file=self.output, 
          flush=True)
