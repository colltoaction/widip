from typing import Any, Callable

type T = Any
type B = Any
type FoliatedObject[T, B] = tuple[T, B]

def p_functor[T, B](obj: FoliatedObject[T, B]) -> B:
    """Maps an object to its base index (the 'fibre' it belongs to)."""
    return obj[1]

def vertical_map[T, B](obj: FoliatedObject[T, B], f: Callable[[T], T]) -> FoliatedObject[T, B]:
    """Transformation where P(f(obj)) == P(obj)."""
    return (f(obj[0]), obj[1])

def cartesian_lift[T, B](obj: FoliatedObject[T, B], new_index: B, lift_fn: Callable[[T, B], T]) -> FoliatedObject[T, B]:
    """Transformation that moves the object from one fibre to another."""
    return (lift_fn(obj[0], new_index), new_index)
