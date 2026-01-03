import asyncio
import sys
from pathlib import Path
from typing import Callable, Any, AsyncIterator

from .io import printer
from .exec import ExecFunctor
from .widish import LOOP_VAR
from .thunk import unwrap, recurse

async def interpreter(runner: Callable, 
                      source: AsyncIterator[tuple[Any, Path | None, Any]],
                      loop: asyncio.AbstractEventLoop,
                      output_handler: Callable = printer):
    """Unified execution loop. Pure in essence, delegating IO to handlers."""
    async for fd, path, input_stream in source:
        try:
            runner_process = runner(fd)
            
            async def compute(rec, *args):
                    inp = (input_stream,) if runner_process.dom else ()
                    res = await runner_process(*inp)
                    # Unwrap returns either the value or a tuple of values
                    final = await unwrap(loop, res)
                    await output_handler(rec, final)
                    return final

            await recurse(compute, None, loop)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if __debug__: raise e
