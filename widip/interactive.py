import asyncio
import sys
from pathlib import Path
from yaml import YAMLError
from typing import IO, Callable, Any, AsyncIterator
from io import StringIO

from .exec import flatten, ExecFunctor
from .thunk import unwrap
from .files import repl_read


async def printer(res: Any):
    filtered = await flatten(res)
    if filtered:
        print(*filtered, sep="\n", flush=True)


async def reader(source: AsyncIterator[tuple[Any, Path | None, IO[str]]]) -> tuple[Any, Path | None, IO[str]]:
    try:
        return await anext(source)
    except StopAsyncIteration:
        raise EOFError


async def read_single(fd: Any, path: Path | None, runner: ExecFunctor, args: list[str]) -> AsyncIterator[tuple[Any, Path | None, IO[str]]]:
    if not sys.stdin.isatty():
        stdin_content = await runner.loop.run_in_executor(None, sys.stdin.read)
    else:
        stdin_content = ""
    combined = "\n".join(args)
    if stdin_content:
        if combined: combined += "\n"
        combined += stdin_content
    yield fd, path, StringIO(combined)


async def read_shell(runner: ExecFunctor, file_name: str) -> AsyncIterator[tuple[Any, Path | None, IO[str]]]:
    loop = runner.loop
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


async def interpreter(runner: ExecFunctor, compiler: Callable, source: AsyncIterator[tuple[Any, Path | None, IO[str]]]):
    async for fd, path, input_stream in source:
        try:
            if isinstance(path, Path) and __debug__:
                from .files import diagram_draw
                diagram_draw(path, fd)

            compiled_d = compiler(fd, path=path)
            runner_process = runner(compiled_d)
            
            # Domain defines input handling
            if runner_process.dom:
                inp = (input_stream,)
            elif isinstance(input_stream, StringIO) and not input_stream.getvalue():
                # pass constants from dom
                inp = tuple(x.name for x in compiled_d.dom)
            else:
                inp = ()

            res = await unwrap(runner_process(*inp))
            await printer(res)

        except KeyboardInterrupt:
            print(file=sys.stderr)
        except YAMLError as e:
            print(e, file=sys.stderr)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if __debug__: raise e
