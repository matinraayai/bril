import json
import sys

from cfg import block_map, edges, add_terminators, add_entry
from form_blocks import form_blocks


def calculate_dominated_map(func):
    """
    Given a BRIL function, computes a mapping between each block inside the func and the
    set of blocks that dominate it.
    """
    # Get the blocks, and ensure it has an entry block, and add terminators at the end of each block
    blocks = block_map(form_blocks(func['instrs']))
    add_entry(blocks)
    add_terminators(blocks)
    # Get the predecessors graph
    predecessor_map, _ = edges(blocks)
    # Remove the entry block from the iteration, as we know it dominates everything
    blocks_without_entry = {name: b for (name, b) in blocks.items() if name != list(blocks.keys())[0]}
    # Initially, map all blocks to each other, except the entry block, which maps only to itself
    dominated_map = {block: {b for b in blocks} for block in blocks}
    dominated_map[list(blocks.keys())[0]] = {list(blocks.keys())[0]}
    changed = True
    while changed:
        changed = False
        for block in blocks_without_entry:
            # dom[vertex] = {vertex} ∪ ⋂{dom[p] for p in vertex.preds}
            current_dominated_map = {block} | set.intersection(*[dominated_map[p] for p in predecessor_map[block]])

            # Replace the entry if it has changed
            if dominated_map[block] != current_dominated_map:
                dominated_map[block] = current_dominated_map
                changed = True
    return dominated_map


def calculate_dominator_map(dominated_map):
    """
    Given a dominated mapping, inverts the dominated mapping to represent the mapping between
    each block and a set of blocks that it dominates.
    """
    dominator_map = {block: set() for block in dominated_map}
    for block, dominators in dominated_map.items():
        for dominator in dominators:
            dominator_map[dominator].add(block)
    return dominator_map


def calculate_dominator_frontier(func, dominator_map):
    """
    Given a function map and a dominator map relation, computes the dominance frontier.
    """
    blocks = block_map(form_blocks(func['instrs']))
    # Get the successors graph
    add_entry(blocks)
    add_terminators(blocks)
    _, successor_map = edges(blocks)

    dominator_frontier = {}
    for block, dominated_blocks in dominator_map.items():
        # Find all successors of blocks dominated by the current block
        dominated_blocks_successors = set()
        for dominated in dominated_blocks:
            dominated_blocks_successors.update(successor_map[dominated])
        # Find all non-strictly dominated successors by the current block
        # You're in the frontier if you're not strictly dominated by the
        # current block.
        dominator_frontier[block] = {dominated_block_successor for dominated_block_successor in
                                     dominated_blocks_successors
                                     if
                                     dominated_block_successor not in dominated_blocks or dominated_block_successor == block}

    return dominator_frontier


def calculate_dominator_tree(dominator_map):
    """
    Given a dominator map relation, creates the dominator tree by calculating the immediate dominance relation
    """
    strict_dominator_map = {block: {dominated_block for dominated_block in dominated_blocks if dominated_block != block}
                            for block, dominated_blocks in dominator_map.items()}
    dominator_tree = {block: set() for block in dominator_map}

    for a, a_strict_dominated_blocks in strict_dominator_map.items():
        for b in a_strict_dominated_blocks:
            if not a_strict_dominated_blocks.union(strict_dominator_map[b]):
                dominator_tree[a].add(b)

    return dominator_tree


if __name__ == '__main__':
    module = json.load(sys.stdin)
    for f in module['functions']:
        dominated_map = calculate_dominated_map(f)
        # Calculate the mapping between each block and a set of blocks it dominates by
        # inverting the dominated_map
        dominator_map = calculate_dominator_map(dominated_map)
        if sys.argv[1] == 'dom':
            # Format the dominated map in json
            print(json.dumps(
                {k: sorted(list(v)) for k, v in dominated_map.items()},
                indent=2, sort_keys=True,
            ))
        elif sys.argv[1] == 'front':
            dominator_frontier = calculate_dominator_frontier(f, dominator_map)
            # Format the output in json
            print(json.dumps(
                {k: sorted(list(v)) for k, v in dominator_frontier.items()},
                indent=2, sort_keys=True,
            ))
        elif sys.argv[1] == 'tree':
            dominator_tree = calculate_dominator_tree(dominator_map)
            print(json.dumps(
                {k: sorted(list(v)) for k, v in dominator_tree.items()},
                indent=2, sort_keys=True,
            ))
        else:
            pass
