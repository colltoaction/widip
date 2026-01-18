"""Python integration for computer module

Provides Python function integration with computational diagrams.
"""

from discopy import python
from .core import Program, Data

class PythonFunction(Program):
    """Wrapper for Python functions as computational programs"""
    def __init__(self, func, name=None):
        self.func = func
        super().__init__(name or func.__name__)
        
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

def to_python(diagram):
    """Convert diagram to Python function
    
    Args:
        diagram: Diagram to convert
        
    Returns:
        Python function
    """
    return python.Function(diagram.dom, diagram.cod, lambda *args: diagram(*args))

__all__ = ['PythonFunction', 'to_python']
