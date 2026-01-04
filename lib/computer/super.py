from .core import Language2

async def interpreter(pipeline, source_gen, loop, capture_output):
    """
    Async interpreter that consumes source_gen, processes it via pipeline,
    and sends results to capture_output.
    """
    if hasattr(source_gen, '__aiter__'):
        async for item in source_gen:
            res = pipeline(item)
            # If pipeline is async, await it
            if hasattr(res, '__await__'):
                res = await res
            await capture_output(None, res)
    else:
        # Fallback for sync iterables?
        pass

def interpreter_box(*args, **kwargs):
    pass

def specializer(*args, **kwargs):
    pass

def specializer_box(*args, **kwargs):
    pass
