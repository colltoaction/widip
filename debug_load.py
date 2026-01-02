from widip.loader import load_file
import sys

try:
    d = load_file("examples/countdown.yaml")
    print(d)
    # If possible, inspect inner structure
    # This might print the Discopy diagram
    for box in d.boxes:
        print(f"Box: {box.name}, Data: {getattr(box, 'data', 'N/A')}")
except Exception as e:
    print(e)
