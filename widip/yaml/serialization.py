
# --- Anchor Registry ---
import contextvars
from contextlib import contextmanager

_ANCHORS: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("anchors", default={})

def get_anchor(name: str) -> Any | None:
    return _ANCHORS.get().get(name)

@contextmanager
def register_anchor(name: str, value: Any):
    old = _ANCHORS.get()
    token = _ANCHORS.set({**old, name: value})
    try:
        yield
    finally:
        _ANCHORS.reset(token)

def set_anchor(name: str, value: Any):
    _ANCHORS.set({**_ANCHORS.get(), name: value})
