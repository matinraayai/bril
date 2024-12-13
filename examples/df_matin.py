import sys
import json
from form_blocks import form_blocks
import cfg


def fmt(val):
    """
    Guess a good way to format a data flow value. (Works for sets and
    dicts, at least.)
    """
    if isinstance(val, set):
        if val:
            return ', '.join(v for v in sorted(val))
        else:
            return '∅'
    elif isinstance(val, dict):
        if val:
            return ', '.join('{}: {}'.format(k, v)
                             for k, v in sorted(val.items()))
        else:
            return '∅'
    else:
        return str(val)


def get_defs(block):
    """
    A set of variables defined in a block; This is the "KILL" set for liveness analysis
    """
    # return instructions with a dest field
    return {i['dest'] for i in block if 'dest' in i}


def get_uses_with_no_defs(block):
    """
    A set of variables used before being defined inside the basic block; This is the "GEN" set for liveness analysis
    """
    defs = set()
    out = set()
    # iterate over the instructions, and find any variable that was used but not defined at each point
    for i in block:
        out.update(v for v in i.get('args', []) if v not in defs)
        if 'dest' in i:
            defs.add(i['dest'])
    return out


def liveness_analysis(module):
    """
    Performs a liveness analysis using the work list algorithm
    """
    for func in module['functions']:
        # Form the CFG and add terminators to the end of the blocks
        blocks = cfg.block_map(form_blocks(func['instrs']))
        cfg.add_terminators(blocks)
        # Get the predecessor and successor graphs
        predecessor_map, successor_map = cfg.edges(blocks)

        # Initialize the work list algorithm variables
        # The work list is a FIFO queue here
        work_list = list(blocks.keys())
        live_outs = {block_name: set() for block_name in blocks}
        live_ins = {block_name: set() for block_name in blocks}

        # Start from the exit block, and traverse the CFG, updating the work list in case the out set of the
        # block has changed
        # The algorithm will stop when all the blocks don't get updated
        while len(work_list) != 0:
            block_name = work_list.pop(0)
            # Update the live-outs set using the meet (merge) operator
            # The union of the live-ins of all successor blocks is set to be the live-outs
            # of the current block
            live_outs[block_name].update(*[live_ins[n] for n in successor_map[block_name]])
            # Update the live-ins set using the transfer operator
            current_live_ins = get_uses_with_no_defs(blocks[block_name]).union(
                live_outs[block_name] - get_defs(blocks[block_name]))

            if current_live_ins != live_ins[block_name]:
                live_ins[block_name] = current_live_ins
                work_list += predecessor_map[block_name]

        for block_name in blocks:
            print('{}:'.format(block_name))
            print('  in: ', fmt(live_ins[block_name]))
            print('  out:', fmt(live_outs[block_name]))


if __name__ == '__main__':
    liveness_analysis(json.load(sys.stdin))
