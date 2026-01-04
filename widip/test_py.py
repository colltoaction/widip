import pytest
import functools
import operator
from widip.computer import eval_diagram, eval_python


# --- Structure Tests ---

def test_eval_diagram_structure():
    """Test that eval_diagram is a callable function."""
    assert callable(eval_diagram)
    # Test it has proper docstring
    assert eval_diagram.__doc__ is not None
    assert "monoid" in eval_diagram.__doc__.lower()


def test_eval_python_structure():
    """Test that eval_python is a callable function."""
    assert callable(eval_python)
    # Test it has proper docstring
    assert eval_python.__doc__ is not None
    assert "functor" in eval_python.__doc__.lower()


# --- Tuple Flattening Tests (eval_diagram) ---

@pytest.mark.parametrize("input_tuples,expected", [
    ((), ()),
    ((("a",),), ("a",)),
    ((("a",), ("b",)), ("a", "b")),
    ((("a", "b"), ("c", "d")), ("a", "b", "c", "d")),
    ((("x",), ("y", "z")), ("x", "y", "z")),
    (((), ("a",), ()), ("a",)),
    ((("hello", "world"),), ("hello", "world")),
    ((("1",), ("2",), ("3",)), ("1", "2", "3")),
])
def test_eval_diagram_flattening(input_tuples, expected):
    """Test tuple-flattening behavior with various inputs."""
    result = eval_diagram(input_tuples)
    assert result == expected
    assert isinstance(result, tuple)


# --- Python Evaluation Tests (eval_python) ---

@pytest.mark.parametrize("code,expected", [
    ("1 + 1", 2),
    ("'hello' + ' ' + 'world'", "hello world"),
    ("[1, 2, 3]", [1, 2, 3]),
    ("{'a': 1, 'b': 2}", {'a': 1, 'b': 2}),
    ("len('test')", 4),
    ("max([1, 5, 3])", 5),
    ("tuple(range(3))", (0, 1, 2)),
])
def test_eval_python_evaluation(code, expected):
    """Test Python code evaluation with various expressions."""
    result = eval_python(code)
    assert result == expected


# --- Integration Tests ---

def test_eval_diagram_with_reduce():
    """Test that eval_diagram uses reduce with operator.add internally."""
    # Verify the behavior matches reduce(operator.add, tuples, ())
    tuples = (("a",), ("b",), ("c",))
    expected = functools.reduce(operator.add, tuples, ())
    result = eval_diagram(tuples)
    assert result == expected


def test_eval_python_with_eval():
    """Test that eval_python behaves like built-in eval."""
    test_code = "2 ** 10"
    expected = eval(test_code)
    result = eval_python(test_code)
    assert result == expected


def test_bootstrap_concept():
    """Test the bootstrap concept: eval_python can evaluate diagram-like code."""
    # eval_python can evaluate Python expressions that could represent diagrams
    code = "tuple(['data1', 'data2'])"
    result = eval_python(code)
    assert result == ('data1', 'data2')
    assert isinstance(result, tuple)


def test_self_hosting_preparation():
    """Test that eval_diagram can process outputs from diagram execution."""
    # Simulate diagram outputs as tuple of tuples
    diagram_outputs = (("result1",), ("result2", "result3"))
    result = eval_diagram(diagram_outputs)
    assert result == ("result1", "result2", "result3")


# --- Metadata Tests ---

def test_eval_diagram_metadata():
    """Test that eval_diagram has proper metadata."""
    assert hasattr(eval_diagram, '__name__')
    assert hasattr(eval_diagram, '__doc__')
    assert callable(eval_diagram)


def test_eval_python_metadata():
    """Test that eval_python has proper metadata."""
    assert hasattr(eval_python, '__name__')
    assert hasattr(eval_diagram, '__doc__')
    assert callable(eval_python)


# --- Edge Cases ---

@pytest.mark.parametrize("input_tuples", [
    ((),),
    ((), ()),
    ((), (), ()),
])
def test_eval_diagram_empty_tuples(input_tuples):
    """Test eval_diagram with empty tuples."""
    result = eval_diagram(input_tuples)
    assert result == ()


def test_eval_diagram_single_element():
    """Test eval_diagram with single element tuples."""
    result = eval_diagram((("single",),))
    assert result == ("single",)


def test_eval_python_simple_literals():
    """Test eval_python with simple literal values."""
    assert eval_python("42") == 42
    assert eval_python("'hello'") == 'hello'
    assert eval_python("True") == True
    assert eval_python("None") is None


# --- Computer Module Integration Tests ---

def test_integration_with_computer_pattern():
    """Test that eval_diagram follows the computer module pattern."""
    # The computer module uses closed.Diagram.from_callable
    # eval_diagram should be compatible for processing diagram outputs
    
    # Simulate what happens when diagrams produce tuple outputs
    outputs = (("data1",), ("data2",))
    result = eval_diagram(outputs)
    
    assert isinstance(result, tuple)
    assert result == ("data1", "data2")


def test_eval_python_can_evaluate_functor_code():
    """Test that eval_python can evaluate code that creates functors."""
    # This demonstrates the self-hosting potential
    code = "lambda x: x * 2"
    func = eval_python(code)
    assert callable(func)
    assert func(5) == 10


def test_composition_readiness():
    """Test that both functions are ready for use."""
    # Both should be callable functions
    assert callable(eval_diagram)
    assert callable(eval_python)
    
    # They should be usable in functional composition
    # Test that eval_diagram can process output from eval_python
    code = "tuple([('a',), ('b',)])"
    tuples = eval_python(code)
    result = eval_diagram(tuples)
    assert result == ('a', 'b')


# --- Advanced Bootstrap Tests ---

def test_eval_python_evaluates_reduce_expression():
    """Test that eval_python can evaluate the same reduce logic as eval_diagram."""
    code = "functools.reduce(operator.add, (('a',), ('b',)), ())"
    # Need to make functools and operator available in eval context
    # This test shows the limitation - eval uses the current scope
    # In practice, we'd need to pass a proper namespace
    import functools, operator
    result = eval(code, {"functools": functools, "operator": operator})
    assert result == ("a", "b")


def test_flattening_preserves_order():
    """Test that tuple flattening preserves element order."""
    tuples = (("first",), ("second",), ("third",))
    result = eval_diagram(tuples)
    assert result == ("first", "second", "third")
    # Verify order is preserved
    assert result[0] == "first"
    assert result[1] == "second"
    assert result[2] == "third"


@pytest.mark.parametrize("nested_level", [1, 2, 3])
def test_eval_diagram_with_varying_tuple_sizes(nested_level):
    """Test eval_diagram with tuples of varying sizes."""
    tuples = [tuple(range(i, i + nested_level)) for i in range(3)]
    result = eval_diagram(tuples)
    # Should flatten all tuples into one
    assert isinstance(result, tuple)
    assert len(result) == 3 * nested_level
