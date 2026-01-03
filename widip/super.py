from __future__ import annotations
import sys
from typing import Any, Callable
from discopy import closed
from .computer import Partial, Language, Program, Data, Computation
from .asyncio import unwrap, recurse

# --- The Interpreter and Specializer diagrams ---

interpreter_box = Program("interpreter", Language @ Language, Language)
specializer_box = Program("specializer", Language @ Language, Language)

@closed.Diagram.from_callable(Language @ Language, Language)
def specializer(program, *args):
    """Partial evaluator / Specializer diagram."""
    return specializer_box(program, *args)

@closed.Diagram.from_callable(Language @ Language, Language)
def interpreter_diagram(program, *args):
    """Interpreter diagram representation."""
    return interpreter_box(program, *args)

# --- Runtime Execution of the Interpreter ---

async def execution_step(pipeline, input_stream, loop, output_handler, rec, *args):
    """Execution step for the interpreter."""
    compiled_process = args[0]
    inp = (input_stream,) if compiled_process.dom else ()
    res = await compiled_process(*inp)
    final = await unwrap(loop, res)
    await output_handler(rec, final)
    return final

async def run_interpreter(pipeline: Callable[[Any], Any], 
                          source: Any, 
                          loop: Any, 
                          output_handler: Callable[[Any, Any], Any]):
    """Unified execution loop. Runs the compiled pipeline on the source inputs."""
    from functools import partial
    async for fd, path, input_stream in source:
        try:
            # The pipeline compiles the YAML (fd) into an executable Process
            runner_process = pipeline(fd)
            # We pass the runner_process as an arg to the step function via partial or direct arg?
            # recursive step signature is (rec, *args).
            # The initial call to recurse passes the initial *args.
            
            step = partial(execution_step, pipeline, input_stream, loop, output_handler)
            await recurse(step, runner_process, loop)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if __debug__: raise e
