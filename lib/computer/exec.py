from __future__ import annotations
from typing import Any, TypeVar, Dict, Callable
from discopy import closed, symmetric, frobenius
from .asyncio import run_command, unwrap
import discopy
from . import python

T = TypeVar("T")
Process = python.Function
Process.type_checking = False

# --- Execution Context ---
_EXEC_CTX = __import__('contextvars').ContextVar("exec_ctx")

class ExecContext:
    def __init__(self, hooks: Dict[str, Callable], executable: str, loop: Any):
        self.hooks, self.executable, self.loop = hooks, executable, loop
        self.anchors = {}

# --- Leaf Execution ---

def exec_box(box: closed.Box) -> Process:
    """Executes a leaf box (Data or Program)."""
    dom = any_ty(len(box.dom))
    cod = any_ty(len(box.cod))
    
    # Generic property access helper
    def get_attr(obj, name, default=None):
        return getattr(obj, name, default)

    # Program box logic
    async def prog_fn(*args):
        ctx = _EXEC_CTX.get()
        memo = {}
        unwrapped_args = []
        for stage in args:
            unwrapped_args.append(await unwrap(stage, ctx.loop, memo))
        
        # Choice/Guard logic: skip on None input
        if len(dom) > 0 and unwrapped_args and unwrapped_args[0] is None:
             return None
        
        # Determine box properties (handling generic Box and YamlBox)
        box_name = box.name
        box_kind = get_attr(box, 'kind', box_name)
        args_data = get_attr(box, 'args', ())
        if not args_data:
             # Try getting value from YamlBox
             args_data = get_attr(box, 'value', None)
             if args_data is None: args_data = ()
             else: args_data = (args_data,)

        stdin_val = unwrapped_args[0] if unwrapped_args else None
        if len(unwrapped_args) > 1: stdin_val = unwrapped_args
        
        # --- Dispatch based on Kind/Name ---
        
        box_name = box.name
        box_kind = get_attr(box, 'kind', box_name)
        # print(f"DEBUG: exec_box name='{box_name}' kind='{box_kind}' args={args_data}", file=sys.stderr)

        if box_kind == "Anchor" or box_name.lower() == "anchor" or box_name.startswith("Anchor"):
            name = get_attr(box, 'anchor_name')
            # Extract name from string if needed (e.g. "Anchor(hello)")
            if name is None and "(" in box_name:
                name = box_name.split("(")[1].rstrip(")")
            
            # Extract 'inside' from args or nested
            inside = None
            if len(args_data) >= 2:
                 name, inside = args_data
            elif len(args_data) == 1:
                 # If name already found, arg is 'inside'. Otherwise arg is 'name'.
                 if name: inside = args_data[0]
                 else: name = args_data[0]
            
            if inside is None:
                 inside = get_attr(box, 'nested')
            
            # print(f"DEBUG: Setting anchor '{name}'", file=sys.stderr)
            if name:
                ctx.anchors[name] = inside
            
            # Execute inside process ensuring we use the same context/loop
            if inside:
                proc = exec_functor(inside)
                
                # Prepare arguments matching process domain
                arg_val = stdin_val
                if arg_val is None and len(proc.dom) > 0:
                     arg_val = b"" if len(proc.dom) == 1 else tuple([b""] * len(proc.dom))
                
                # Tuplify input if needed
                args_in = (arg_val,)
                if len(proc.dom) > 1 and isinstance(arg_val, tuple):
                     args_in = arg_val
                elif len(proc.dom) == 0:
                     args_in = ()
                     
                res = await unwrap(proc(*args_in), ctx.loop, memo)
                result = res
            else:
                result = stdin_val

        elif box_kind == "Alias" or box_name == "alias":
            name = get_attr(box, 'anchor_name') or (args_data[0] if args_data else None)
            if name not in ctx.anchors:
                raise ValueError(f"Unknown anchor: {name}")
                
            # DO NOT call exec_functor(ctx.anchors[name]) immediately!
            # That would cause infinite recursion for recursive definitions.
            # Instead, return a proxy that resolves it when called.
            async def alias_proxy(*args_in):
                ctx_inner = _EXEC_CTX.get()
                memo_inner = {}
                # Resolve the aliased process lazily
                proc = exec_functor(ctx_inner.anchors[name])
                
                # Handling arguments (same as in standard leaf execution)
                if not args_in and len(proc.dom) > 0:
                     args_in = (b"",) if len(proc.dom) == 1 else (tuple([b""] * len(proc.dom)),)
                
                return await unwrap(proc(*args_in), ctx_inner.loop, memo_inner)

            result = alias_proxy

        elif box_name == "print":
             from .asyncio import printer
             await printer(None, stdin_val, ctx.hooks)
             result = () if not cod else stdin_val
        elif box_name == "read_stdin":
             result = ctx.hooks['stdin_read']()
        elif type(box).__name__ == "Data" or box_kind == "Scalar":
             # Handle Data box or Scalar YamlBox
             if box_kind == "Scalar": 
                  result = get_attr(box, 'value')
             else:
                  result = box.name
        elif type(box).__name__ == "Partial":
             from .core import Partial
             # Returning the box itself as a 'partial' application (callable/process)
             result = box 
        elif box_name == "ackermann":
             from .hyper_extended import ackermann_impl
             m, n = map(int, stdin_val) if isinstance(stdin_val, tuple) else (0, 0)
             result = ackermann_impl(m, n)
        elif box_name == "busy_beaver":
             from .hyper_extended import busy_beaver_impl
             n = int(stdin_val) if stdin_val is not None else 0
             result = busy_beaver_impl(n)
        elif box_name == "fast_growing":
             from .hyper_extended import fast_growing
             alpha, n = map(int, stdin_val) if isinstance(stdin_val, tuple) else (0, 0)
             result = fast_growing(alpha, n)
        elif box_name == "supercompile":
             from .super_extended import Supercompiler
             # For supercompile, stdin_val might be a diagram or its name
             sc = Supercompiler()
             result = sc.supercompile(stdin_val)
        elif box_name == "specializer":
             from .super_extended import specialize
             if isinstance(stdin_val, tuple) and len(stdin_val) >= 2:
                  prog, data = stdin_val[0], stdin_val[1]
                  # data needs to be wrapped in a Diagram if it's just a Box or Scalar
                  if not hasattr(data, 'boxes'):
                       from .core import Data
                       data = Data(data)
                  result = specialize(prog, data)
             else:
                  result = stdin_val
        elif box_name == "choice":
             if len(args_data) >= 2:
                  branch1, branch2 = args_data
                  # Determine truthiness of stdin_val
                  # If result is bytes/string, non-empty is generally true
                  # If it's a number (bool), use it.
                  cond = False
                  if stdin_val:
                       if isinstance(stdin_val, (int, bool)): cond = bool(stdin_val)
                       elif isinstance(stdin_val, (str, bytes)):
                            # Check if it looks like "0", "false", etc.
                            s = str(stdin_val).lower().strip()
                            cond = s not in ["0", "false", "null", "none", ""]
                       else:
                            cond = True
                  
                  target = branch1 if cond else branch2
                  result = await execute(target, ctx.hooks, ctx.executable, ctx.loop, stdin_val)
             else:
                  result = stdin_val
        elif box_name in ["decrement", "dec", "r"]:
             # Predecessor
             try: result = int(stdin_val) - 1
             except: result = 0
        elif box_name in ["increment", "succ", "s"]:
             # Successor
             try: result = int(stdin_val) + 1
             except: result = 1
        elif box_name in ["multiply", "mul"]:
             # Product
             if isinstance(stdin_val, tuple) and len(stdin_val) >= 2:
                  result = int(stdin_val[0]) * int(stdin_val[1])
             else:
                  result = 0
        elif box_name in ["check_exponent", "test_zero", "0?"]:
             # Truthiness test
             try: result = int(stdin_val) == 0
             except: result = False
        elif box_name == "python_interpreter":
             # Eval
             try: result = eval(stdin_val)
             except: result = stdin_val
        elif box_kind.lower() == "stream":
             from .core import Program
             # Execute each item in the stream sequentially with CLEARED context
             stream_items = get_attr(box, 'nested', [])
             if not stream_items and args_data: stream_items = args_data[0]
             
             last_res = None
             if len(cod) == 1: 
                  # Accumulate results if codomain is 1 (Language)
                  results = []
                  for item in stream_items:
                       # CLEAR ANCHORS before each document
                       ctx.anchors.clear()
                       item_proc = exec_functor(item)
                       
                       item_in = (stdin_val,) if len(item_proc.dom) > 0 else ()
                       if len(item_proc.dom) > 1 and isinstance(stdin_val, tuple): item_in = stdin_val
                       
                       r = await unwrap(item_proc(*item_in), ctx.loop, memo)
                       if r is not None: results.append(r)
                  
                  if not results: result = None
                  elif len(results) == 1: result = results[0]
                  else: 
                       # Merge results
                       from .asyncio import to_bytes
                       valid = []
                       for r in results:
                            b = await to_bytes(r, ctx.loop, ctx.hooks)
                            valid.append(b)
                       result = b"".join(valid)
             else:
                  # If codomain is 0 or >1, just run
                  for item in stream_items:
                       # Do not clear anchors effectively allowing them to persist across stream items
                       # ctx.anchors.clear() 
                       item_proc = exec_functor(item)
                       item_in = (stdin_val,) if len(item_proc.dom) > 0 else ()
                       if len(item_proc.dom) > 1 and isinstance(stdin_val, tuple): item_in = stdin_val
                       await unwrap(item_proc(*item_in), ctx.loop, memo)
                  result = ()
        else:
             # Regular Command Execution
             # Tagged boxes: use tag as command name if name is "Tagged"
             cmd_name = box_name
             if box_kind == "Tagged":
                  cmd_name = get_attr(box, 'tag', box_name)
                  # Special handling for known core tags
                  if cmd_name == "Data":
                       # Extract value from nested
                       nested = get_attr(box, 'nested')
                       if getattr(nested, 'kind', '') == 'Scalar':
                            result = get_attr(nested, 'value')
                            return discopy.utils.tuplify(result) if len(cod) > 1 else result
                  
                  # For tagged boxes, arguments might be in the 'nested' structure
                  # If nested is a Scalar/Sequence, we should extract values
                  nested = get_attr(box, 'nested')
                  if nested:
                       # Simple extraction logic: if nested is Scalar, use its value as arg
                       nested_kind = getattr(nested, 'kind', '')
                       if nested_kind == 'Scalar':
                            val = get_attr(nested, 'value')
                            if val is not None: args_data = (val,)
                       elif hasattr(nested, 'boxes'):
                            # It's a Diagram (Sequence or Mapping)
                            # We treat it as a Sequence of arguments
                            extracted_args = []
                            for b in nested.boxes:
                                 # We expect Scalar boxes or equivalent
                                 b_kind = getattr(b, 'kind', getattr(b, 'name', ''))
                                 if b_kind == 'Scalar' or b.name == 'Scalar':
                                      val = getattr(b, 'value', None)
                                      if val is None and hasattr(b, 'data'): val = b.data # legacy
                                      if val is not None: extracted_args.append(str(val))
                                 elif hasattr(b, 'name'):
                                      # Fallback: simple scalar boxes might just use name
                                      extracted_args.append(b.name)
                            if extracted_args:
                                 args_data = tuple(extracted_args)
             
             result = await run_command(lambda x: x, ctx.loop, cmd_name, args_data, stdin_val, ctx.hooks)
        
        # Enforce DisCoPy Process return conventions
        n_out = len(cod)
        if n_out == 0: return ()
        if n_out == 1:
             if isinstance(result, tuple):
                  return result[0] if len(result) > 0 else None
             return result
        return discopy.utils.tuplify(result)
    return Process(prog_fn, dom, cod)

def any_ty(n: int):
    return python.Ty(*([object] * n))

def exec_swap(box: symmetric.Swap) -> Process:
    async def swap_fn(a, b):
        ctx = _EXEC_CTX.get()
        return (await unwrap(b, ctx.loop), await unwrap(a, ctx.loop))
    return Process(swap_fn, any_ty(len(box.dom)), any_ty(len(box.cod)))

# --- Dispatcher ---

def exec_dispatch(box: Any) -> Process:
    # 1. Handle algebraic operations regardless of exact class
    name = getattr(box, 'name', None)
    if name == "Δ": return exec_copy(box)
    if name == "μ": return exec_merge(box)
    if name == "ε": return exec_discard(box)
    if hasattr(box, 'is_swap') and box.is_swap: return exec_swap(box)

    # 2. Handle known box categories
    if isinstance(box, (closed.Box, symmetric.Box, frobenius.Box)):
        if isinstance(box, symmetric.Swap): return exec_swap(box)
        return exec_box(box)
    
    # 3. Default to identity
    return Process.id(any_ty(len(getattr(box, 'dom', closed.Ty()))))

# --- Core Combinators Execution ---

def exec_copy(box: closed.Box) -> Process:
    n = getattr(box, 'n', 2)
    if n == 0:
        return exec_discard(box)

    def copy_fn(x):
        loop = _EXEC_CTX.get().loop
        from .asyncio import unwrap
        import io
        import asyncio

        # Use a Future to share the result of the loader
        fut = loop.create_future()
        started = False

        async def loader():
             val = await unwrap(x, loop)
             if val is None: return (None,) * n
             if hasattr(val, 'read'):
                  content = await val.read()
                  return tuple(io.BytesIO(content) for _ in range(n))
             return (val,) * n

        async def getter(i):
             nonlocal started
             if not started:
                 started = True
                 try:
                     res = await loader()
                     fut.set_result(res)
                 except Exception as e:
                     fut.set_exception(e)
             
             res_tuple = await fut
             return res_tuple[i]
             
        return tuple(getter(i) for i in range(n))
    return Process(copy_fn, any_ty(1), any_ty(n))

def exec_merge(box: closed.Box) -> Process:
    """Handles merging (μ). Concatenates results."""
    n = getattr(box, 'n', 2)
    async def merge_fn(*args):
        from .asyncio import unwrap, to_bytes
        loop = _EXEC_CTX.get().loop
        # Await all inputs
        results = [await unwrap(a, loop) for a in args]
        
        # Filter None and join
        valid = []
        for r in results:
             if r is not None:
                  # Convert to bytes for safe concatenation
                  b = await to_bytes(r, loop, _EXEC_CTX.get().hooks)
                  valid.append(b)
        
        if not valid: return None
        # Join with newline if they look like lines, or empty?
        # Shell tools usually output trailing newlines. Concatenating them safely:
        # If we use empty separator, we rely on tools providing newlines.
        return b"".join(valid) 
    return Process(merge_fn, any_ty(n), any_ty(1))

def exec_discard(box: closed.Box) -> Process:
    async def discard_fn(*args):
        from .asyncio import unwrap
        loop = _EXEC_CTX.get().loop
        import asyncio
        for a in args: 
             val = await unwrap(a, loop)
             if val is not None and hasattr(val, 'read'):
                 if asyncio.iscoroutinefunction(val.read): await val.read()
                 else:
                      res = val.read()
                      if asyncio.iscoroutine(res): await res
        return ()
    return Process(discard_fn, any_ty(len(box.dom)), any_ty(0))
class UniversalObMap:
    def __getitem__(self, _): return object
    def get(self, key, default=None): return object

from weakref import WeakKeyDictionary
_FUNCTOR_CACHE = WeakKeyDictionary()

def _exec_functor_impl(diag: closed.Diagram) -> Process:
    import sys
    sys.setrecursionlimit(100000) # Ensure high limit for deep recursion
    
    if diag in _FUNCTOR_CACHE:
        return _FUNCTOR_CACHE[diag]
        
    from discopy.closed import Functor
    f = Functor(ob=UniversalObMap(), ar=exec_dispatch, cod=python.Category())
    res = f(diag)
    _FUNCTOR_CACHE[diag] = res
    return res

from .yaml import Composable
exec_functor = Composable(_exec_functor_impl)

async def execute(diag: closed.Diagram, hooks: Dict[str, Callable],
                  executable: str = "python3", loop: Any = None, stdin: Any = None,
                  memo: dict | None = None) -> Any:
    """Execute a diagram using the async evaluation loop."""
    if loop is None:
        import asyncio
        loop = asyncio.get_event_loop()
    if memo is None: memo = {}
    
    ctx = ExecContext(hooks, executable, loop)
    token = _EXEC_CTX.set(ctx)
    try:
        proc = exec_functor(diag)
        # Default to empty bytes if no stdin provided but domain is non-empty
        active_stdin = stdin
        if active_stdin is None and len(proc.dom) > 0:
            active_stdin = b""
        arg = (active_stdin,) if proc.dom else ()
        res = await unwrap(proc(*arg), loop, memo)
        return res
    finally:
        try:
            _EXEC_CTX.reset(token)
        except ValueError: pass

class titi_runner:
    """Class-based context manager for running titi diagrams."""
    def __init__(self, hooks: Dict[str, Callable], executable: str = "python3", loop: Any = None):
        if loop is None:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None # Will be handled in __enter__ if needed

        self.hooks, self.executable, self.loop = hooks, executable, loop

    def __enter__(self):
        if self.loop is None:
            import asyncio
            self.loop = asyncio.get_event_loop()
            
        def runner(diag: closed.Diagram, stdin: Any = None):
            return execute(diag, self.hooks, self.executable, self.loop, stdin)
        return runner, self.loop

    def __exit__(self, *args):
        pass

compile_exec = exec_functor
__all__ = ['execute', 'ExecContext', 'exec_dispatch', 'Process', 'titi_runner', 'compile_exec']
