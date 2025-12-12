import pathlib
import io

from discopy.closed import Ty, Diagram, Box, Id, Functor

from .loader import repl_read


def files_ar(ar: Box) -> Diagram:
    """Uses IO to read a file or dir with the box name as path"""
    if not ar.name.startswith("file://"):
        return ar

    try:
        return file_diagram(ar.name.lstrip("file://"))
    except IsADirectoryError:
        print("is a dir")
        return ar

def file_diagram(file_name) -> Diagram:
    path = pathlib.Path(file_name)

    if path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
        try:
            from .im2diag import image_to_yaml
            yaml_content = image_to_yaml(str(path))
            fd = repl_read(io.StringIO(yaml_content))
            return fd
        except ImportError:
            print("widip.im2diag not found or dependencies missing. Cannot load image.")
            # Fallback or re-raise?
            raise
        except Exception as e:
            print(f"Error converting image to diagram: {e}")
            raise

    fd = repl_read(path.open())
    # TODO TypeError: Expected closed.Diagram, got monoidal.Diagram instead
    # fd = replace_id_f(path.stem)(fd)
    return fd

def diagram_draw(path, fd):
    fd.draw(path=str(path.with_suffix(".jpg")),
            textpad=(0.3, 0.1),
            fontsize=12,
            fontsize_types=8)

files_f = Functor(lambda x: Ty(""), files_ar)
