from discopy import closed
from ..common import service, TitiBox
from ..core import Language

from ..common import service, TitiBox, set_anchor

Copy = service("Δ", Language, Language @ Language, draw_as_spider=True)
Discard = service("ε", Language, closed.Ty(), draw_as_spider=True)
Swap = service("ς", Language @ Language, Language @ Language, draw_as_spider=True)

# Native Implementations
import inspect

async def _ensure_awaited(val):
    if inspect.isawaitable(val):
        return await val
    return val

async def _discard(stdin):
    stdin = await _ensure_awaited(stdin)
    if hasattr(stdin, 'read'):
        while await stdin.read(8192): pass
    elif isinstance(stdin, (list, tuple)):
        for item in stdin: await _discard(item)
    return ()

async def _copy(stdin):
    stdin = await _ensure_awaited(stdin)
    if hasattr(stdin, 'read'):
        # For safety with streams, we must materialize them to copy
        # Ideally we'd use a Tee, but simpler to read fully for now
        content = await stdin.read()
        import io
        return (io.BytesIO(content), io.BytesIO(content))
    return (stdin, stdin)

async def _swap(stdin):
    stdin = await _ensure_awaited(stdin)
    a, b = stdin
    return (b, a)

set_anchor("ε", _discard)
set_anchor("Δ", _copy)
set_anchor("ς", _swap)

# IO Services
def ReadStdin():
    return TitiBox("cat", Language, Language, data=())

def Printer():
    return closed.Id(Language)

__all__ = ["Copy", "Discard", "Swap", "ReadStdin", "Printer"]
