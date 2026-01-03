from .composer import compose
from .parse import parse
from .construct import construct


load = parse >> compose >> construct
