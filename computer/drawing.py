"""Drawing module for computational diagrams

Provides drawing functionality for diagrams using discopy.
"""

from discopy import drawing

def draw(diagram, **params):
    """Draw a diagram using discopy's drawing functionality
    
    Args:
        diagram: The diagram to draw
        **params: Additional parameters for drawing
        
    Returns:
        The drawing result
    """
    return diagram.draw(**params)

# Alias for compatibility
diagram_draw = draw

__all__ = ['draw', 'diagram_draw']
