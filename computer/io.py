"""I/O primitives for computer module

Provides I/O operations for computational diagrams.
"""

from .core import Language, Data

class IO(Data):
    """I/O box for input/output operations"""
    def __init__(self, dom, cod):
        super().__init__(dom, cod)
        self.name = "IO"

def read_input():
    """Read input operation
    
    Returns:
        Input data
    """
    return input()

def write_output(data):
    """Write output operation
    
    Args:
        data: Data to output
    """
    print(data)
    return data

__all__ = ['IO', 'read_input', 'write_output']
