from titi.files import repl_read

yaml_str = "!xargs { test, -eq, 0 }"

try:
    d = repl_read(yaml_str)
    print(f"Diagram: {d}")
    print(f"Boxes: {d.boxes}")
    for box in d.boxes:
        print(f"Box Name: {box.name}")
        if hasattr(box, 'data'):
             print(f"Box Value Type: {type(box.data)}")
             print(f"Box Value: {box.data}")
except Exception as e:
    print(e)
