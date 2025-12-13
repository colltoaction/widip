from discopy.closed import Box, Ty
from discopy.python import Function

class ShellBox(Box):
    """Abstract class for Shell Boxes."""
    pass

class ConstBox(ShellBox):
    """Box producing a constant string value."""
    def __init__(self, value, dom=Ty(), cod=Ty("str")):
        self.value = value
        # We ensure the name is what we expect
        super().__init__(name="const", dom=dom, cod=cod, data=value)

class RunBox(ShellBox):
    """Box running a program."""
    def __init__(self, dom=Ty("str"), cod=Ty("str")):
        super().__init__(name="run", dom=dom, cod=cod)

# Define other boxes as needed
