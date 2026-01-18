"""Composition utilities for computer module

Provides composition operations for computational diagrams.
"""

from .core import Sequential, Concurrent, Data

def sequential_compose(*diagrams):
    """Sequentially compose diagrams
    
    Args:
        *diagrams: Diagrams to compose sequentially
        
    Returns:
        Composed diagram
    """
    if not diagrams:
        return None
    result = diagrams[0]
    for d in diagrams[1:]:
        result = result >> d
    return result

def parallel_compose(*diagrams):
    """Compose diagrams in parallel (tensor product)
    
    Args:
        *diagrams: Diagrams to compose in parallel
        
    Returns:
        Composed diagram
    """
    if not diagrams:
        return None
    result = diagrams[0]
    for d in diagrams[1:]:
        result = result @ d
    return result

__all__ = ['sequential_compose', 'parallel_compose']
