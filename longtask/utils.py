import os
import sys


class OutputManager(object):

    def __init__(self, disable=True):
        self.disable = disable

    def __enter__(self):
        if self.disable:
            self.stdnull = self.stderr = self.stdout = sys.stderr = sys.stdout = open(os.devnull, 'w')
        else:
            self.stdout = sys.stdout
            self.stderr = sys.stderr
        return self

    def __exit__(self, type , value , traceback):
        if self.disable:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            self.stdnull.close()
