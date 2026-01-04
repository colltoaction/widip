"""
Parser Integration for Monoidal Computer

This module integrates the lex/yacc YAML parser with the monoidal computer's
categorical execution model, enabling:
1. Parsing YAML to AST using the C-based parser
2. Converting AST to categorical diagrams
3. Executing diagrams in the monoidal computer
"""

from __future__ import annotations
from typing import Any
from discopy import closed, frobenius
from .core import Language
from .yaml.representation import Scalar, Sequence, Mapping, Alias, Anchor, Node, YamlBox
import subprocess
import json
import os


class YAMLParserBridge:
    """
    Bridge between the C-based lex/yacc parser and Python categorical diagrams.
    """
    
    def __init__(self, parser_path: str = None):
        """
        Initialize the parser bridge.
        
        Args:
            parser_path: Path to the yaml_parser executable
        """
        if parser_path is None:
            # Default to lib/computer/_yaml_parser
            base_dir = os.path.dirname(os.path.abspath(__file__))
            parser_path = os.path.join(base_dir, "_yaml_parser")
        
        self.parser_path = parser_path
        
        # Check if parser exists
        if not os.path.exists(self.parser_path):
            raise FileNotFoundError(
                f"YAML parser not found at {self.parser_path}. "
                f"Run the parse.yaml build script to compile it."
            )
    
    def parse_to_ast(self, yaml_source: str) -> dict:
        """
        Parse YAML source to AST using the C parser.
        
        Args:
            yaml_source: YAML source code as string
        
        Returns:
            AST as a dictionary
        """
        # Run the parser as a subprocess
        try:
            result = subprocess.run(
                [self.parser_path],
                input=yaml_source.encode('utf-8'),
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8')
                raise ValueError(f"Parser error: {error_msg}")
            
            # Parse the output (currently prints AST, we'd need to modify to output JSON)
            output = result.stdout.decode('utf-8')
            return self._parse_ast_output(output)
        
        except subprocess.TimeoutExpired:
            raise TimeoutError("Parser timed out")
        except FileNotFoundError:
            raise FileNotFoundError(f"Parser executable not found: {self.parser_path}")
    
    def _parse_ast_output(self, output: str) -> dict:
        """
        Parse the AST output from the C parser.
        
        The current parser prints a tree structure. We need to convert this
        to a structured dictionary.
        
        Args:
            output: Raw output from parser
        
        Returns:
            Structured AST dictionary
        """
        lines = output.strip().split('\n')
        
        # Simple parser for the indented tree structure
        root = {'type': 'root', 'children': []}
        stack = [(-1, root)]
        
        for line in lines:
            # Count leading spaces
            indent = len(line) - len(line.lstrip())
            content = line.strip()
            
            if not content:
                continue
            
            # Parse node type and value
            if ':' in content:
                node_type, value = content.split(':', 1)
                node = {
                    'type': node_type.strip(),
                    'value': value.strip(),
                    'children': []
                }
            else:
                node = {
                    'type': content,
                    'children': []
                }
            
            # Find parent based on indentation
            while stack and stack[-1][0] >= indent:
                stack.pop()
            
            if stack:
                parent = stack[-1][1]
                parent['children'].append(node)
            
            stack.append((indent, node))
        
        return root['children'][0] if root['children'] else root
    
    def ast_to_diagram(self, ast: dict) -> closed.Diagram:
        """
        Convert AST to a categorical diagram.
        
        Args:
            ast: AST dictionary from parse_to_ast
        
        Returns:
            Categorical diagram representing the YAML structure
        """
        return self._convert_node(ast)
    
    def _convert_node(self, node: dict) -> closed.Diagram:
        """
        Recursively convert an AST node to a diagram.
        
        Args:
            node: AST node dictionary
        
        Returns:
            Diagram representing this node
        """
        node_type = node.get('type', '')
        
        if node_type == 'SCALAR':
            # Scalar values become Scalar boxes
            value = node.get('value', '')
            # TODO: Extract tag/anchor from AST if available
            return Scalar(tag="", value=value)
        
        elif node_type == 'SEQUENCE':
            # Sequences become nested Sequence boxes
            children = node.get('children', [])
            if not children:
                return Sequence(frobenius.Id(Node), tag="")
            
            # Compose all children sequentially
            # Each child is a Diagram(Node, Node)
            diagrams = [self._convert_node(child) for child in children]
            result = diagrams[0]
            for diag in diagrams[1:]:
                result = result >> diag
            return Sequence(result, tag="")
        
        elif node_type == 'MAPPING':
            # Mappings become nested Mapping boxes with tensor product structure
            children = node.get('children', [])
            if not children:
                return Mapping(frobenius.Id(Node), tag="")
            
            # Children come in pairs (key, value)
            diagrams = []
            for i in range(0, len(children), 2):
                if i + 1 < len(children):
                    key_diag = self._convert_node(children[i])
                    val_diag = self._convert_node(children[i + 1])
                    diagrams.append(key_diag @ val_diag)
            
            if not diagrams:
                return Mapping(frobenius.Id(Node), tag="")
            
            result = diagrams[0]
            for diag in diagrams[1:]:
                result = result @ diag
            return Mapping(result, tag="")
        
        elif node_type == 'ALIAS':
            # Aliases become Alias boxes
            alias_name = node.get('value', '')
            if alias_name.startswith("*"): alias_name = alias_name[1:]
            return Alias(alias_name)
        
        elif node_type == 'ANCHOR':
            # Anchors wrap their children
            anchor_name = node.get('value', '')
            if anchor_name.startswith("&"): anchor_name = anchor_name[1:]
            children = node.get('children', [])
            
            if children:
                inner_diag = self._convert_node(children[0])
            else:
                inner_diag = frobenius.Id(Node)
            
            return Anchor(anchor_name, inner_diag)
        
        elif node_type == 'TAG':
            # TAG node acts as a wrapper
            tag_name = node.get('value', '')
            if tag_name.startswith("!"):
                tag_name = tag_name[1:]
            children = node.get('children', [])
            
            if children:
                inner_diag = self._convert_node(children[0])
            else:
                inner_diag = frobenius.Id(Node)
                
            # Use specific YamlBox kind "Tagged" to let construct.py handle the tag
            return YamlBox("Tagged", dom=inner_diag.dom, cod=inner_diag.cod, kind="Tagged", tag=tag_name, nested=inner_diag)

        else:
            # Unknown node type - return identity on Node
            return frobenius.Id(Node)
    
    def parse(self, yaml_source: str) -> closed.Diagram:
        """
        Complete pipeline: parse YAML source to categorical diagram.
        
        Args:
            yaml_source: YAML source code
        
        Returns:
            Categorical diagram ready for execution
        """
        ast = self.parse_to_ast(yaml_source)
        return self.ast_to_diagram(ast)


# --- Integration with Supercompilation ---

def parse_and_supercompile(yaml_source: str, parser: YAMLParserBridge = None) -> closed.Diagram:
    """
    Parse YAML and apply supercompilation optimizations.
    
    Args:
        yaml_source: YAML source code
        parser: Optional parser bridge instance
    
    Returns:
        Optimized categorical diagram
    """
    if parser is None:
        parser = YAMLParserBridge()
    
    # Parse to diagram
    diagram = parser.parse(yaml_source)
    
    # Apply supercompilation
    from .super_extended import Supercompiler
    sc = Supercompiler()
    optimized = sc.supercompile(diagram)
    
    return optimized


# --- Integration with Hypercomputation ---

def parse_and_hypercompute(yaml_source: str, parser: YAMLParserBridge = None) -> closed.Diagram:
    """
    Parse YAML and prepare for hypercomputational execution.
    
    This adds support for transfinite operations and hypercomputational primitives.
    
    Args:
        yaml_source: YAML source code
        parser: Optional parser bridge instance
    
    Returns:
        Diagram with hypercomputational enhancements
    """
    if parser is None:
        parser = YAMLParserBridge()
    
    # Parse to diagram
    diagram = parser.parse(yaml_source)
    
    # Detect and enhance hypercomputational patterns
    # (This is a placeholder - full implementation would analyze the diagram)
    
    return diagram


# --- Build Script Support ---

def build_parser(lib_dir: str = None) -> bool:
    """
    Build the YAML parser using lex and yacc.
    
    This executes the equivalent of the parse.yaml build script.
    
    Args:
        lib_dir: Directory containing yaml.l and yaml.y files
    
    Returns:
        True if build succeeded, False otherwise
    """
    if lib_dir is None:
        lib_dir = os.path.dirname(os.path.abspath(__file__))
    
    yaml_l = os.path.join(lib_dir, "yaml.l")
    yaml_y = os.path.join(lib_dir, "yaml.y")
    
    try:
        # Run lex
        subprocess.run(
            ["lex", yaml_l],
            cwd=lib_dir,
            check=True,
            capture_output=True
        )
        
        # Run yacc
        subprocess.run(
            ["yacc", "-d", yaml_y],
            cwd=lib_dir,
            check=True,
            capture_output=True
        )
        
        # Compile
        subprocess.run(
            ["cc", "lex.yy.c", "y.tab.c", "-lfl", "-o", "yaml_parser"],
            cwd=lib_dir,
            check=True,
            capture_output=True
        )
        
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False
    except FileNotFoundError as e:
        print(f"Build tool not found: {e}")
        return False


__all__ = [
    'YAMLParserBridge',
    'parse_and_supercompile',
    'parse_and_hypercompute',
    'build_parser',
]
