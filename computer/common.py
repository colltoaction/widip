"""Common utilities for computer module

Provides common helper functions and utilities.
"""

from .core import Data, Program

def compose(*functions):
    """Compose multiple functions
    
    Args:
        *functions: Functions to compose
        
    Returns:
        Composed function
    """
    def composed(x):
        result = x
        for f in functions:
            result = f(result)
        return result
    return composed

def identity(x):
    """Identity function
    
    Args:
        x: Input value
        
    Returns:
        Same value
    """
    return x

__all__ = ['compose', 'identity']
