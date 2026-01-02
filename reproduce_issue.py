import sys
from itertools import batched
from pathlib import Path
sys.path.append("/home/colltoaction/GitHub/widip")

from nx_yaml import nx_compose_all
import widip.loader as loader
import widip.hif as hif

filename = "tests/test_complex_expr.test.yaml"
with open(filename) as f:
    node = nx_compose_all(f)

# The root starts at cursor (0, node)
cursor = (0, node)

# Traverse to root document content
root_cursor = hif.step(cursor, "next")
if not root_cursor:
    print("No root found")
    sys.exit(1)

root_data = hif.get_node_data(root_cursor)
print(f"Root kind: {root_data['kind']}")

# Root is a sequence.
children = list(hif.iterate(root_cursor))
print(f"Root has {len(children)} children in sequence")

for i, child in enumerate(children):
    kind = hif.get_node_data(child)['kind']
    # If the child is a mapping (the loop step), inspect it
    # Note: FizzBuzz.yaml structure is: [1, Anchor(Mapping)]
    # Anchor wraps the object. So we might see 'mapping' directly or via anchor?
    # incidental_to_diagram handles anchor wrapping. hif.iterate gives the raw nodes.
    # get_node_data(child) gives dictionary with "kind", "anchor", etc.
    
    print(f"Child {i}: kind={kind}")

    if kind == 'sequence':
         print(f"--- Inspecting Sequence at child {i} ---")
         seq_items = list(hif.iterate(child))
         for k, seq_item in enumerate(seq_items):
             seq_data = hif.get_node_data(seq_item)
             seq_kind = seq_data["kind"]
             print(f"  Seq Item {k}: kind={seq_kind}, anchor={seq_data.get('anchor')}")
             
             if seq_kind == 'mapping':
                 print(f"    --- Inspecting Mapping ---")
                 mapping_items = list(hif.iterate(seq_item))
                 print(f"    Mapping has {len(mapping_items)} items in hif stream")
                 for j, item in enumerate(mapping_items):
                     data = hif.get_node_data(item)
                     val = data.get('value', 'N/A')
                     print(f"      Item {j}: kind={data['kind']}, tag={data.get('tag')}, val='{val}'")

    if kind == 'mapping':
        print(f"--- Inspecting Mapping at child {i} ---")
        mapping_items = list(hif.iterate(child))
        print(f"Mapping has {len(mapping_items)} items in hif stream")
        for j, item in enumerate(mapping_items):
            data = hif.get_node_data(item)
            val = data.get('value', 'N/A')
            print(f"  Item {j}: kind={data['kind']}, tag={data.get('tag')}, val='{val}'")

