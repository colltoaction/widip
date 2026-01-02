from widip.files import file_diagram
from widip.compiler import SHELL_COMPILER
from widip.widish import SHELL_RUNNER
import asyncio

async def main():
    try:
        yaml_d = file_diagram("examples/countdown.yaml")
        print(f"YAML Diagram items: {yaml_d.boxes}")
        compiled_d = SHELL_COMPILER(yaml_d)
        print(f"Compiled Diagram boxes: {compiled_d.boxes}")
        widish_d = SHELL_RUNNER(compiled_d)
        print(f"Widish Diagram boxes: {widish_d.boxes}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
