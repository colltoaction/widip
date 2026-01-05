from typing import Any, Callable, List
from discopy import cat
from computer.asyncio import pipe_async, tensor_async, loop_var, unwrap
import asyncio

class Ty(list):
    """A list of python types."""
    def __init__(self, *args):
        # Flatten args
        flat = []
        for a in args:
             if isinstance(a, Ty): flat.extend(a)
             elif isinstance(a, (list, tuple)): flat.extend(a)
             else: flat.append(a)
        super().__init__(flat)

    def tensor(self, other):
        if isinstance(other, Ty):
            return Ty(*super().__add__(list(other)))
        if isinstance(other, Function):
            return Function.id(self) @ other
        return NotImplemented

    def __add__(self, other):
        return self.tensor(other)

    def __matmul__(self, other):
        return self.tensor(other)

    def __repr__(self):
        return f"Ty({', '.join(map(str, self))})"
    
    def __pow__(self, n):
        return Ty(*(list(self) * n))

class Function:
    """A function with domain and codomain."""
    def __init__(self, inside: Callable, dom: Ty, cod: Ty):
        self.inside = inside
        self.dom = dom
        self.cod = cod
    
    def __call__(self, *args):
        return self.inside(*args)

    def then(self, other):
        async def composed(*args):
             loop = loop_var.get()
             if loop is None:
                  try: loop = asyncio.get_running_loop()
                  except RuntimeError: loop = asyncio.new_event_loop()
             
             # pipe_async(left, right, loop, *args)
             return await pipe_async(self.inside, other.inside, loop, *args)
        
        return Function(composed, self.dom, other.cod)

    def tensor(self, other):
        if isinstance(other, Ty):
            other = Function.id(other)
            
        async def parallel(*args):
             loop = loop_var.get()
             if loop is None:
                  try: loop = asyncio.get_running_loop()
                  except RuntimeError: loop = asyncio.new_event_loop()
             
             # tensor_async(left, dom, right, loop, *args)
             return await tensor_async(self.inside, self.dom, other.inside, loop, *args)
        
        return Function(parallel, self.dom @ other.dom, self.cod @ other.cod)

    def __rshift__(self, other):
        return self.then(other)
    
    def __matmul__(self, other):
        return self.tensor(other)

    def __rmatmul__(self, other):
        if isinstance(other, Ty):
             return Function.id(other) @ self
        return NotImplemented

    def __rshift__(self, other):
        return self.then(other)
    
    def __matmul__(self, other):
        return self.tensor(other)

    @staticmethod
    def id(dom):
         async def identity(*args):
              if len(args) == 1: return args[0]
              return args
         return Function(identity, dom, dom)

class Category(cat.Category):
    ob = Ty
    ar = Function
