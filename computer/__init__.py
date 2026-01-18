# Computer module - Computational model from "Programs as Diagrams"

from .core import (
    Language,
    Language2,
    Data,
    Program,
    Constant,
    Sequential,
    Concurrent,
    Pair,
    Cast,
    Swap,
    Copy,
    Discard,
    Trace,
    Exec,
    Eval,
    Partial,
    Merge,
    Computation
)

__all__ = [
    'Language',
    'Language2',
    'Data',
    'Program',
    'Constant',
    'Sequential',
    'Concurrent',
    'Pair',
    'Cast',
    'Swap',
    'Copy',
    'Discard',
    'Trace',
    'Exec',
    'Eval',
    'Partial',
    'Merge',
    'Computation'
]

# Placeholder for service_map (referenced in titi/__init__.py)
service_map = {}
