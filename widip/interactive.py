import asyncio
import sys
import inspect
from pathlib import Path
from yaml import YAMLError

from discopy.utils import tuplify

from .files import file_diagram, repl_read
from .widish import SHELL_RUNNER
from .compiler import SHELL_COMPILER
from .thunk import unwrap, force_execution, flatten, is_awaitable


async def apply_inp(r, val):
    if is_awaitable(r):
        r = await unwrap(r)

    if callable(r):
        res = r(val)
        return await unwrap(res)
    return r

async def run_process(runner, inp):
    if isinstance(runner, tuple):
        lazy_result = await asyncio.gather(*(apply_inp(r, inp) for r in runner))
        return tuple(lazy_result)
    else:
        return await apply_inp(runner, inp)

async def async_exec_diagram(yaml_d, path, *shell_program_args):
    loop = asyncio.get_running_loop()

    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path, yaml_d)

    constants = tuple(x.name for x in yaml_d.dom)
    compiled_d = SHELL_COMPILER(yaml_d)

    if __debug__ and path is not None:
        from .files import diagram_draw
        diagram_draw(path.with_suffix(".shell.yaml"), compiled_d)

    # Run the shell runner to get the computation process/function
    process_result = await unwrap(SHELL_RUNNER(compiled_d)(*constants))
    runner = process_result

    if sys.stdin.isatty():
        inp = ""
    else:
        inp = await loop.run_in_executor(None, sys.stdin.read)

    lazy_result = await run_process(runner, inp)

    # Force execution of the Task(s)
    val = await force_execution(lazy_result)
        
    print(*(tuple(x.rstrip() for x in flatten(tuplify(val)) if x)), sep="\n")


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

            # Execute the runner to get the lazy result
            process_result = await unwrap(SHELL_RUNNER(compiled_d)(*constants))

            # Use empty input for interactive commands if they don't expect stdin?
            # Or pass "" as before.
            lazy_result = await run_process(process_result, "")

            # Force execution
            result = await force_execution(lazy_result)

            print(*(tuple(x.rstrip() for x in flatten(tuplify(result)) if x)), sep="\n")

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
