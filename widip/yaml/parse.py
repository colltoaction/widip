from typing import Any

def parse(source: Any) -> Any:
    """Parse a stream or string using nx_yaml HIF parser."""
    try:
        from nx_yaml import nx_compose_all
    except ImportError:
        raise ImportError("nx_yaml is required for YAML parsing.")
    return nx_compose_all(source)
