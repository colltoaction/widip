import asyncio
import sys
from pathlib import Path
from yaml import YAMLError

from discopy.utils import tuplify

from .files import file_diagram, repl_read
from .widish import SHELL_RUNNER
from .thunk import unwrap
from .compiler import SHELL_COMPILER


async def async_exec_diagram(yaml_d, path, *shell_program_args):
    loop = asyncio.get_running_loop()

    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path, yaml_d)

    # constants = tuple(x.name for x in yaml_d.dom) 
    # Logic moved to after reading input to allow injecting stdin into IO wires
    compiled_d = SHELL_COMPILER(yaml_d)

    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)

    if sys.stdin.isatty():
        inp = ""
    else:
        inp = await loop.run_in_executor(None, sys.stdin.read)
        
    # Bind inputs: Use 'inp' for IO wires, box name for others (constants)
    args = tuple(inp if x.name == "IO" else x.name for x in compiled_d.dom)
    
    runner = SHELL_RUNNER(compiled_d)(*args)
    
    runners = tuplify(runner)
    tasks = []
    immediate_results = []
    
    for r in runners:
        if callable(r):
            # Thunk is now fully bound with inputs, just call it
            tasks.append(r())
        else:
            immediate_results.append(r)
            
    task_results = await asyncio.gather(*map(unwrap, tasks))
    results = tuple(immediate_results) + tuple(task_results)
    
    # Flatten results if needed, though they might be strings
    # Filter out empty strings and Ty() artifacts
    final_output = []
    for res in results:
        for x in tuplify(res):
            if x:
                s = str(x).rstrip()
                if s and "Ty(" not in s:
                     final_output.append(s)

    print(*final_output, sep="\n")


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
            result_ev = SHELL_RUNNER(compiled_d)(*constants)
            result = await unwrap(result_ev)
            print(*(tuple(x.rstrip() for x in tuplify(result) if x)), sep="\n")

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
