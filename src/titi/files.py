import sys
import importlib.resources
from pathlib import Path
from yaml import YAMLError

from discopy.closed import Ty, Diagram, Box, Functor

from nx_yaml import nx_compose_all
from .loader import incidences_to_diagram


def resolve_path(file_name: str) -> Path:
    """
    Resolves a file path by looking in the following order:
    1. Current working directory.
    2. titi/bin (packaged resources).
    3. titi/lib (packaged resources).
    """
    path = Path(file_name)
    if path.exists():
        return path

    # Check packaged bin
    try:
        bin_path = importlib.resources.files("titi") / "bin" / file_name
        if bin_path.exists():
            return bin_path
        # Also check recursively in subdirectories if needed?
        # For now, let's assume flat or explicit relative structure.
        # If the user asked for "yaml/shell.yaml", checking "bin/yaml/shell.yaml" works.
    except Exception:
        pass

    # Check packaged lib
    try:
        lib_path = importlib.resources.files("titi") / "lib" / file_name
        if lib_path.exists():
            return lib_path
    except Exception:
        pass

    # Fallback to checking typical location relative to CWD if packaged check failed but it might be there
    # This handles "bin/yaml/shell.yaml" relative to repo root if running from repo root
    # (which is covered by step 1, but this is for extra safety)

    return path


def repl_read(stream):
    incidences = nx_compose_all(stream)
    return incidences_to_diagram(incidences)


def reload_diagram(path_str):
    print(f"reloading {path_str}", file=sys.stderr)
    try:
        fd = file_diagram(path_str)
        diagram_draw(Path(path_str), fd)
        diagram_draw(Path(path_str+".2"), fd)
    except YAMLError as e:
        print(e, file=sys.stderr)

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
    path = resolve_path(file_name)
    # If resolve_path returned a non-existent path (default), open() will raise appropriate error
    fd = repl_read(path.open())
    return fd

def diagram_draw(path, fd):
    fd.draw(path=str(path.with_suffix(".jpg")),
            textpad=(0.3, 0.1),
            fontsize=12,
            fontsize_types=8)

files_f = Functor(lambda x: Ty(""), files_ar)
