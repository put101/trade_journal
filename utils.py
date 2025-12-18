from typing import List
from datetime import datetime
import pandas as pd
import numpy as np

def green_print(txt):
    print('\033[92m', txt, '\033[0m', flush=True)

def ok(txt):
    green_print('OK: ' + txt)

def yellow_print(txt):
    print('\033[93m', txt, '\033[0m', flush=True)
    
def err(txt):
    yellow_print('ERR: ' + txt)

def pink_print(txt):
    print('\033[95m', txt, '\033[0m', flush=True)
