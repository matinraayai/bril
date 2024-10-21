import json
import sys

from cfg import block_map, edges, add_terminators, add_entry
from form_blocks import form_blocks

def calculate_dom(func):
    # Get the blocks, and ensure it has an entry block, and add terminators at the end of each block
    blocks = block_map(form_blocks(func['instrs']))
    add_entry(blocks)
    add_terminators(blocks)
    # Get the predecessors graph
    predecessor_map, _ = edges(blocks)
    # Initially, map all blocks to each other
    dom_set = {block : {b for b in blocks.items()} for block in blocks.items()}
    # Remove the entry block from the iteration, as we know it dominates everything
    blocks_without_entry = {name: b for (name, b) in blocks.items() if name != list(blocks.keys())[0]}
    changed = True
    while changed:
        changed = False
        for block in blocks_without_entry:
            current_dom = set()
            # dom[vertex] = {vertex} ∪ ⋂{dom[p] for p in vertex.preds}
            current_dom.intersection_update(dom_set[p] for p in predecessor_map[block])
            current_dom.add(block)

            # Replace the entry if it has changed
            if dom_set[block] != current_dom:
                dom_set[block] = current_dom
                changed = True

    return dom_set

if __name__ == '__main__':
    module = json.load(sys.stdin)
    for f in module['functions']:
        dom = calculate_dom(f)
        # Format the DOM in JSON
        print(json.dumps(
            {k: sorted(list(v)) for k, v in dom.items()},
            indent=2, sort_keys=True,
        ))
