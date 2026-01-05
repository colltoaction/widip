"""Unit tests for the YAML parser - simple cases."""

import pytest
from computer.yaml import load


class TestSimpleScalars:
    """Test basic scalar parsing."""
    
    def test_single_scalar(self):
        """Single plain scalar."""
        result = load("hello")
        assert result is not None
    
    def test_quoted_string(self):
        """Double-quoted string."""
        result = load('"hello world"')
        assert result is not None
    
    def test_single_quoted_string(self):
        """Single-quoted string."""
        result = load("'hello world'")
        assert result is not None


class TestSimpleMappings:
    """Test basic mapping structures."""
    
    def test_single_key_value(self):
        """Single key-value pair on one line."""
        result = load("foo: bar")
        assert result is not None
    
    def test_two_key_values_same_level(self):
        """Two key-value pairs at same indentation."""
        yaml_str = """foo: bar
baz: qux"""
        result = load(yaml_str)
        assert result is not None
    
    def test_nested_mapping(self):
        """Nested mapping with indentation."""
        yaml_str = """foo:
  bar: baz"""
        result = load(yaml_str)
        assert result is not None
    
    def test_flow_mapping(self):
        """Flow-style mapping."""
        result = load("{a: b, c: d}")
        assert result is not None


class TestSimpleSequences:
    """Test basic sequence structures."""
    
    def test_flow_sequence(self):
        """Flow-style sequence."""
        result = load("[a, b, c]")
        assert result is not None
    
    def test_block_sequence(self):
        """Block-style sequence."""
        yaml_str = """- a
- b
- c"""
        result = load(yaml_str)
        assert result is not None
    
    def test_nested_sequence(self):
        """Nested sequence."""
        yaml_str = """- - a
  - b
- c"""
        result = load(yaml_str)
        assert result is not None


class TestAnchorsAndAliases:
    """Test anchors and aliases."""
    
    def test_simple_anchor_and_alias(self):
        """Basic anchor and alias."""
        yaml_str = """- &anchor value
- *anchor"""
        result = load(yaml_str)
        assert result is not None


class TestTags:
    """Test tag handling."""
    
    def test_simple_tag(self):
        """Simple tag on scalar."""
        result = load("!str hello")
        assert result is not None
    
    def test_tag_on_sequence(self):
        """Tag on sequence."""
        result = load("!seq [a, b, c]")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
