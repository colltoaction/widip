import sys
from nx_yaml import load

yaml_str = """
!xargs { test, -eq, 0 }
"""
try:
    data = load(yaml_str)
    print(f"Type: {type(data)}")
    print(f"Value: {data}")
except Exception as e:
    print(e)
