import asyncio
import sys
from pathlib import Path
from yaml import YAMLError
from typing import IO, Callable, Any, AsyncIterator
from io import StringIO
from functools import partial

from .exec import ExecFunctor
from .widish import safe_read_str
from .thunk import unwrap, recurse
from .files import repl_read

async def printer(rec, res: Any):
    content = await safe_read_str(res)
    filtered = content.splitlines()
    if filtered:
        print(*filtered, sep="\n", flush=True)

async def read_single(fd: Any, path: Path | None, runner: ExecFunctor, args: list[str], loop: asyncio.AbstractEventLoop) -> AsyncIterator[tuple[Any, Path | None, IO[str]]]:
    if not sys.stdin.isatty():
        stdin_content = await loop.run_in_executor(None, sys.stdin.read)
    else:
        stdin_content = ""
    combined = "\n".join(args)
    if stdin_content:
        if combined: combined += "\n"
        combined += stdin_content
    yield fd, path, StringIO(combined)

async def read_shell(runner: ExecFunctor, file_name: str, loop: asyncio.AbstractEventLoop) -> AsyncIterator[tuple[Any, Path | None, IO[str]]]:
    while True:
        try:
            if not sys.stdin.isatty():
                source_str = await loop.run_in_executor(None, sys.stdin.read)
                if not source_str: break
            else:
                prompt = f"--- !{file_name}\n"
                source_str = await loop.run_in_executor(None, input, prompt)
            
            yield repl_read(source_str), Path(file_name), StringIO("")
            if not sys.stdin.isatty(): break
        except EOFError:
            break

async def interpreter(runner: ExecFunctor, 
                      compiler: Callable, 
                      source: AsyncIterator[tuple[Any, Path | None, IO[str]]],
                      loop: asyncio.AbstractEventLoop,
                      input_handler: Callable = None, 
                      output_handler: Callable = printer):
    
    # Internal logic for dealing with inputs if no handler provided
    def default_input_handler(runner_process, compiled_d, input_stream):
        if runner_process.dom:
             return (input_stream,)
        if isinstance(input_stream, StringIO) and not input_stream.getvalue():
             return tuple(x.name for x in compiled_d.dom)
        return ()
        
    if input_handler is None:
        input_handler = default_input_handler

    async for fd, path, input_stream in source:
        try:
            if isinstance(path, Path) and __debug__:
                from .files import diagram_draw
                diagram_draw(path, fd)

            compiled_d = compiler(fd, compiler, path)
            runner_process = runner(compiled_d)
            
            inp = input_handler(runner_process, compiled_d, input_stream)
            
            async def compute(rec, *args):
                 res = await runner_process(*inp)
                 final = await unwrap(loop, res)
                 await output_handler(rec, final)
                 return final

            await recurse(compute, None, loop)

        except KeyboardInterrupt:
            print(file=sys.stderr)
        except YAMLError as e:
            print(e, file=sys.stderr)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if __debug__: raise e
