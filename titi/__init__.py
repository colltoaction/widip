# Titi - Wiring Diagrams in Python
import sys
import os

# Add lib to PYTHONPATH for the computer module
lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from computer.core import Language, Language2
from computer import service_map, Data, Program
from .exec import Process
