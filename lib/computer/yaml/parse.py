from __future__ import annotations
from typing import Any
from itertools import batched
from discopy import frobenius, monoidal, closed

# Import the C-based parser bridge
from .parser_bridge import YAMLParserBridge




# --- Serialization Primitives (Native DisCoPy Factories) ---
from .representation import (
    Scalar, Alias, Sequence, Mapping, Anchor, Document, Stream, YamlBox,
    Node
)


# --- Parser Implementation using C lex/yacc ---

# Global parser instance (lazy initialization)
_parser_instance = None

def get_parser() -> YAMLParserBridge:
    """Get or create the global parser instance."""
    global _parser_instance
    if _parser_instance is None:
        try:
            _parser_instance = YAMLParserBridge()
        except FileNotFoundError:
            # Parser not built yet
            return None
    return _parser_instance


def parse_box(source_wire):
    """Create a parse box for categorical composition."""
    return frobenius.Box("parse", frobenius.Ty("CharacterStream"), Node)(source_wire)


def impl_parse(source) -> closed.Diagram:
    """
    Native implementation of the YAML parser using C lex/yacc.
    
    This replaces the old nx_yaml implementation with the compiled parser,
    enabling metacompilation and supercompilation.
    """
    # Extract source string
    if hasattr(source, "source") and type(source).__name__ == "CharacterStream":
        source = source.source
    
    if not hasattr(source, 'read') and not isinstance(source, (str, bytes)):
        raise TypeError(f"Expected stream or string, got {type(source)}")
    
    # Convert to string if needed
    if hasattr(source, 'read'):
        source_str = source.read()
        if isinstance(source_str, bytes):
            source_str = source_str.decode('utf-8')
    elif isinstance(source, bytes):
        source_str = source.decode('utf-8')
    else:
        source_str = str(source)
    
    # Try C parser
    parser = get_parser()
    if parser is not None:
        try:
            return parser.parse(source_str)
        except Exception as e:
            raise ValueError(f"Parser error: {e}")
            
    raise ImportError("YAML parser not found. Build it using 'make parser' or 'make bootstrap'")


@frobenius.Diagram.from_callable(frobenius.Ty("CharacterStream"), Node)
def parse(source):
    """
    Traceable parse diagram using C lex/yacc parser.
    
    This is the main entry point for YAML parsing in the monoidal computer.
    It uses the compiled C parser for performance and enables metacompilation.
    """
    if not hasattr(source, 'read') and not isinstance(source, (str, bytes)):
        return parse_box(source)
    return impl_parse(source)


# --- Metacompilation Support ---

def supercompile_parser() -> closed.Diagram:
    """
    Apply supercompilation to the parser itself using Futamura projections.
    
    This demonstrates the monoidal computer's self-metacompilation capability.
    """
    from ..super_extended import Supercompiler
    from ..parser_bridge import YAMLParserBridge
    
    parser = YAMLParserBridge()
    # The parser is already compiled C code, but we can represent it
    # as a categorical diagram for further optimization
    parser_diag = closed.Box("yaml_parser", closed.Ty("YAML"), closed.Ty("AST"))
    
    sc = Supercompiler()
    return sc.supercompile(parser_diag)


__all__ = ['parse', 'impl_parse', 'supercompile_parser']
