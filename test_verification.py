from widip.yaml import Scalar, YAML_COMPILER
from discopy import closed

def test_scalar_compilation():
    print("Testing scalar with value 'Hello' and tag 'str'")
    try:
        s = Scalar("str", "Hello")
        # Check dom and cod
        print(f"Scalar dom: {s.dom}")
        print(f"Scalar cod: {s.cod}")

        compiled = YAML_COMPILER(s)
        print("Compilation success")
        print(f"Compiled box: {compiled}")
        print(f"Compiled dom: {compiled.dom}")
        print(f"Compiled cod: {compiled.cod}")

        # Expected behavior:
        # Scalar dom: Ty('str', 'Hello')
        # Scalar cod: Ty('str') << Ty('str')
        # Compiled box should be Discard('str') @ Data('Hello', ...)

    except Exception as e:
        print(f"Compilation failed: {e}")
        import traceback
        traceback.print_exc()

    print("\nTesting scalar with no value and tag 'str'")
    try:
        s = Scalar("str", None)
        print(f"Scalar dom: {s.dom}")
        print(f"Scalar cod: {s.cod}")

        compiled = YAML_COMPILER(s)
        print("Compilation success")
        print(f"Compiled box: {compiled}")
        print(f"Compiled dom: {compiled.dom}")
        print(f"Compiled cod: {compiled.cod}")

    except Exception as e:
        print(f"Compilation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scalar_compilation()
