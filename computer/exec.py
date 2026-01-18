# Execution module for computer package

from .core import Program, Data
from discopy import python

class Process(python.Function):
    """Process class for executing computational programs"""
    def __init__(self, diagram, *args, **kwargs):
        self.diagram = diagram
        super().__init__(diagram.dom, diagram.cod, lambda *x: diagram(*x), *args, **kwargs)

def titi_runner(diagram):
    """Run a diagram using titi execution model
    
    Args:
        diagram: The diagram to execute
        
    Returns:
        Execution result
    """
    # Convert diagram to executable form and run
    if hasattr(diagram, 'eval'):
        return diagram.eval()
    return diagram

__all__ = ['Process', 'titi_runner']
