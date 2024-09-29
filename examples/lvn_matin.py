import json
import sys

from form_blocks import form_blocks
from util import flatten


def is_commutative(op):
    """
    Returns true whether the op's args can be sorted or not.
    """
    return op in {"add", "mul", "eq", "fadd", "fmul", "feq", "and", "or"}


class ValueNumberTable:
    def __init__(self):
        # Mapping between a "renamed" variable and its value
        self.variable_to_value_map = {}
        # Mapping between an expression and its value
        self.expr_to_value_map = {}
        # Mapping between a value and its canonical variable name
        self.value_to_canonical_variable_map = {}
        # Next value to be assigned
        self.next_value = 0
        # A mapping between the number of times a variable has been (re-)defined
        self.num_defs_per_variable = {}

    def _get_renamed_variable_name(self, variable):
        var_name = variable
        # Append a number to the variable name in case it is
        if variable in self.num_defs_per_variable and self.num_defs_per_variable[variable] > 1:
            var_name += str(self.num_defs_per_variable[variable])
        return var_name

    def get_canonical_of_value(self, val):
        return self.value_to_canonical_variable_map[val]

    def get_or_create_use_value(self, variable):
        # For when the variable is a live-in of the block
        if variable not in self.num_defs_per_variable:
            self.num_defs_per_variable[variable] = 0
        var_name = self._get_renamed_variable_name(variable)
        if var_name not in self.variable_to_value_map:
            self.variable_to_value_map[var_name] = self.next_value
            self.value_to_canonical_variable_map[self.next_value] = var_name
            self.next_value += 1
        return self.variable_to_value_map[var_name]

    def get_def_value(self, instr):
        if "dest" in instr:
            dest_var = instr["dest"]
            expr = self.get_expr_of_instr(instr)
            # Lookup the expression of this instruction defining the dest; If it's already
            # there, return the value it is assigned to; Otherwise, create a new value for the def
            if expr in self.expr_to_value_map:
                renamed_dest_var = self._get_renamed_variable_name(dest_var)
                # Also record the def value if not already in the variable map
                if renamed_dest_var not in self.variable_to_value_map:
                    self.variable_to_value_map[renamed_dest_var] = self.expr_to_value_map[expr]
                return self.expr_to_value_map[expr]
            else:
                return None
        else:
            return None

    def get_or_create_def_value(self, instr):
        if "dest" in instr:
            dest_variable = instr["dest"]
            expr = self.get_expr_of_instr(instr)
            # Increment the number of times this variable has been defined
            if dest_variable not in self.num_defs_per_variable:
                self.num_defs_per_variable[dest_variable] = 0
            self.num_defs_per_variable[dest_variable] += 1
            # Add the renamed variable name to the mapping between variable names and values
            dest_var_name = self._get_renamed_variable_name(dest_variable)
            self.variable_to_value_map[dest_var_name] = self.next_value
            # Lookup the expression of this instruction defining the dest; If it's already
            # there, return the value it is assigned to; Otherwise, create a new value for the def
            if expr not in self.expr_to_value_map:
                self.value_to_canonical_variable_map[self.next_value] = dest_var_name
                self.expr_to_value_map[expr] = self.next_value
                self.next_value += 1
            return self.expr_to_value_map[expr]
        else:
            return None

    def get_expr_of_instr(self, inst):
        expr = []
        is_comm = False
        if "op" in inst:
            expr.append(inst["op"])
            is_comm = is_commutative(inst["op"])
            if inst["op"] == "const":
                expr.append(inst["value"])
                expr.append(inst["type"])
        args = []
        if "args" in inst:
            for arg in inst["args"]:
                args.append(self.get_or_create_use_value(arg))
        if is_comm:
            args = sorted(args)
        expr += args
        return tuple(expr)


def lvn_block_pass(block):
    number_table = ValueNumberTable()
    for instr in block:
        arg_vals = []
        dest_val = None
        change_to_id = False
        if "args" in instr:
            for arg in instr["args"]:
                arg_vals.append(number_table.get_or_create_use_value(arg))

        dest_val = number_table.get_def_value(instr)
        # We don't have a value defined for this def; Create one.
        if "dest" in instr and dest_val is None:
            dest_val = number_table.get_or_create_def_value(instr)
        else:
            change_to_id = True
        # Re-materialize the instruction by renaming its operands
        if len(arg_vals) != 0:
            for i, arg_val in enumerate(arg_vals):
                instr["args"][i] = number_table.get_canonical_of_value(arg_val)
        if "dest" in instr:
            if change_to_id:
                instr.update({
                        'op': 'id',
                        'args': [number_table.get_canonical_of_value(dest_val)],
                    })
            else:
                instr["dest"] = number_table.get_canonical_of_value(dest_val)


if __name__ == '__main__':
    bril = json.load(sys.stdin)
    for func in bril['functions']:
        blocks = list(form_blocks(func['instrs']))
        for block in blocks:
            lvn_block_pass(
                block
            )
        func['instrs'] = flatten(blocks)
    json.dump(bril, sys.stdout, indent=2, sort_keys=True)
