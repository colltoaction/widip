import asyncio
import sys
from pathlib import Path
from yaml import YAMLError
from typing import IO
from io import StringIO

from discopy.utils import tuplify

from .files import file_diagram, repl_read
from .exec import EXEC as SHELL_RUNNER
from .widish import Process
from .thunk import unwrap
from .compiler import SHELL_COMPILER
from .computer import Language


def flatten(x: IO | list | tuple | str | None) -> list[str]:
    if x is None: return []
    if hasattr(x, 'read'):
        content = x.read()
        return content.splitlines() if content else []
    if isinstance(x, (list, tuple)):
        res = []
        for item in x: res.extend(flatten(item))
        return res
    return [str(x)]


async def async_exec_diagram(yaml_d, path, *shell_program_args):
    loop = asyncio.get_running_loop()

    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path, yaml_d)

    compiled_d = SHELL_COMPILER(yaml_d)
    
    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)
    
    runner_process = SHELL_RUNNER(compiled_d)
    
    # Map shell_program_args to the initial input
    # If the diagram expects input, use shell_program_args or stdin
    initial_args = list(shell_program_args) if shell_program_args else []
    
    # Read stdin if available
    stdin_content = ""
    if not sys.stdin.isatty():
        stdin_content = await loop.run_in_executor(None, sys.stdin.read)
    
    # Combine args and stdin into one inputs list? 
    # Or depends on process domain.
    # If domain is simple IO (length 1), we combine everything into one Stream.
    # If domain is wider, we might need distribution strategy.
    # For now, following shelling convention: arguments + stdin -> single input stream
    
    combined_input_str = "\n".join(initial_args)
    if stdin_content:
        if combined_input_str: combined_input_str += "\n"
        combined_input_str += stdin_content
        
    input_stream = StringIO(combined_input_str)
    
    # Input tuple for the process
    # Just pass the stream as the single input. 
    # If dom is 0, we pass nothing? 
    # If dom is > 1, we duplicates? Or pass multiple streams?
    # Simplest assumption: Main diagram takes 1 IO wire.
    inp = (input_stream,)
    
    # If dom is 0 (State), we don't pass arguments properly? 
    # But usually shells start with IO.
    if not runner_process.dom:
         inp = ()
         
    # Execute
    if inp:
        res = await unwrap(runner_process(*inp))
    else:
        res = await unwrap(runner_process())
    
    # Filter out dead branches (None) and print result
    filtered = flatten(res)
    if filtered:
        print(*filtered, sep="\n", flush=True)


async def async_command_main(command_string, *shell_program_args):
    fd = repl_read(command_string)
    # No file path associated with command string
    await async_exec_diagram(fd, None, *shell_program_args)


async def async_widish_main(file_name, *shell_program_args):
    fd = file_diagram(file_name)
    path = Path(file_name)
    await async_exec_diagram(fd, path, *shell_program_args)


async def async_shell_main(file_name):
    path = Path(file_name)
    loop = asyncio.get_running_loop()

    while True:
        try:
            if not sys.stdin.isatty():
                source = await loop.run_in_executor(None, sys.stdin.read)
                if not source:
                    break
            else:
                prompt = f"--- !{file_name}\n"
                source = await loop.run_in_executor(None, input, prompt)

            yaml_d = repl_read(source)
            if __debug__:
                from .files import diagram_draw
                diagram_draw(path, yaml_d)
            source_d = SHELL_COMPILER(yaml_d)
            compiled_d = source_d
            # compiled_d = SHELL_COMPILER(source_d)
            # if __debug__:
            #     diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)
            constants = tuple(x.name for x in compiled_d.dom)
            result = await unwrap(SHELL_RUNNER(compiled_d)(*constants))
            print(*(tuplify(result)), sep="\n")

            if not sys.stdin.isatty():
                break
        except EOFError:
            if sys.stdin.isatty():
                print("⌁", file=sys.stderr)
            break
        except KeyboardInterrupt:
            print(file=sys.stderr)
        except YAMLError as e:
            print(e, file=sys.stderr)
