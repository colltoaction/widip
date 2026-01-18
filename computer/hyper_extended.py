"""Extended hypercomputation features for computer module

Provides extended hypercomputation capabilities beyond basic oracles.
"""

from .core import Program, Data
from .hyper import Oracle

class HyperOracle(Oracle):
    """Extended oracle with additional hypercomputation capabilities"""
    def __init__(self, problem, level=1):
        super().__init__(problem)
        self.level = level
        
    def consult(self, query):
        """Consult the oracle with a query
        
        Args:
            query: Query to ask the oracle
            
        Returns:
            Oracle's answer
        """
        # Placeholder - real hyperoracle would solve undecidable problems
        return None

class InfiniteComputation(Program):
    """Represents an infinite computation
    
    Can represent non-terminating or unbounded computations.
    """
    def __init__(self, name):
        super().__init__(name)
        self.is_infinite = True

__all__ = ['HyperOracle', 'InfiniteComputation']
