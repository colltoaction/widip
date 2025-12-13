import sys
from typing import get_origin
import discopy.utils

# Define patch
original_assert_isinstance = discopy.utils.assert_isinstance

def patched_assert_isinstance(object_, cls: type | tuple[type, ...]):
    """ Monkey-patched assert_isinstance to handle parameterized generics. """
    classes = cls if isinstance(cls, tuple) else (cls, )
    cleaned_classes = []
    for c in classes:
        origin = get_origin(c)
        cleaned_classes.append(origin if origin is not None else c)

    # We do the check ourselves to avoid calling original with parameterized generics
    if not any(isinstance(object_, c) for c in cleaned_classes):
        # Determine what to pass to original to generate error
        # If we pass cleaned classes, message is less precise but valid.
        return original_assert_isinstance(object_, tuple(cleaned_classes))

# Patch utils
discopy.utils.assert_isinstance = patched_assert_isinstance

# Patch all loaded modules that imported assert_isinstance
for module_name, module in list(sys.modules.items()):
    if module_name.startswith("discopy"):
        if hasattr(module, "assert_isinstance"):
            setattr(module, "assert_isinstance", patched_assert_isinstance)
