import sys
import json
from form_blocks import form_blocks
from util import flatten

def trivial_dce_pass(f) -> bool:
    """
    Removes dead code by detection variables that have been defined but not used across the entire function.
    """
    program_modified = False
    changed = True
    blocks = list(form_blocks(f['instrs']))
    # Run until convergence
    while changed:
        # Get the operands of each instr inside the block
        # and mark it as used
        changed = False
        # Set of operands used in the entire function
        used_operands = set()
        for block in blocks:
            for instr in block:
                if "args" in instr:
                    for arg in instr["args"]:
                        used_operands.add(arg)

        # Reconstruct the block, and only add
        # instructions with a dest that is not used
        new_block = []
        for block in blocks:
            for instr in block:
                if "dest" in instr and instr["dest"] not in used_operands:
                    changed |= True
                else:
                    new_block.append(instr)
            # Copy over the old block to the new block
            block[:] = new_block
    # Re-assemble the program back together
    func['instrs'] = flatten(blocks)
    return program_modified


def remove_unused_defs_pass(f) -> bool:
    """
    Removes any defs of a variable that is not used inside a single block.
    """
    program_modified = False
    changed = True
    blocks = list(form_blocks(f['instrs']))
    # Run until convergence
    while changed:
        # Get the operands of each instr inside the block
        # and mark it as used
        changed = False
        # Reconstruct the block, and only add
        # instructions with a dest that is not used
        for block in blocks:
            # Mapping between a variable and the index of the last instruction defining it without using it
            variable_to_last_def_with_no_use_map = {}

            dead_instrs = set()
            for i, instr in enumerate(block):
                # If any of the last defs now have a use, remove them from the map
                if "args" in instr:
                    for arg in instr['args']:
                        del variable_to_last_def_with_no_use_map[arg]

                # If the instr has a dest:
                if 'dest' in instr:
                    dest = instr['dest']
                    # Check if it is re-defining any of the instructions inside the map and mark it for removal
                    # we can't remove it inside the loop to avoid mutation
                    if dest in variable_to_last_def_with_no_use_map:
                        dead_instrs.add(variable_to_last_def_with_no_use_map[dest])
                        changed |= True
                    # Add the def to be kept track of its use
                    variable_to_last_def_with_no_use_map[dest] = i
            block[:] = [i for i in block if i not in dead_instrs]
    # Re-assemble the program back together
    func['instrs'] = flatten(blocks)
    return program_modified


if __name__ == '__main__':
    bril = json.load(sys.stdin)
    for func in bril['functions']:
        trivial_dce_pass(func)
        remove_unused_defs_pass(func)
    json.dump(bril, sys.stdout, indent=2, sort_keys=True)
