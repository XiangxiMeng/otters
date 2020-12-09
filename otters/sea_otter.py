import parso
from parso.tree import NodeOrLeaf, Leaf
from parso.python.tree import PythonNode
from jedi.api import classes, helpers
from jedi.api.project import Project
from jedi.inference import InferenceState
from jedi.inference.references import find_references
from jedi.inference.context import ModuleContext
from jedi.inference.value.module import ModuleValue
from typing import List

grammar = parso.load_grammar(version='3.6')
project = Project(path='')
inference_state = InferenceState(project)


def get_leaves_of_node(n: NodeOrLeaf) -> List[Leaf]:
    """
    get all leaves under a certain node.

    :param n: node
    :return: list of leaves
    """
    next_sibling = n.get_next_sibling()
    end_leaf = None if next_sibling is None else next_sibling.get_first_leaf()
    leaf = n.get_first_leaf()
    ls = []
    while leaf != end_leaf:
        ls.append(leaf)
        leaf = leaf.get_next_leaf()
    return ls


def simple_dependency(code: str):
    """
    parse code, extract variables then match their dependencies.

    :param code: string
    :return: {var_name: list of name}
    """
    module = grammar.parse(code)
    graph = dict()
    for stmt in module.children:
        if stmt.type != 'simple_stmt':
            continue
        leaves = get_leaves_of_node(stmt)
        graph[leaves[0].value] = leaves[2:]
    return graph


def get_usage(context: ModuleContext, node: NodeOrLeaf, state: InferenceState) -> List[classes.Name]:
    names = find_references(context, node, True)

    definitions = [classes.Name(state, n) for n in names]
    definitions = [d for d in definitions if not d.in_builtin_module()]
    return helpers.sorted_definitions(definitions)


def get_codes(stmts: List[PythonNode]) -> str:
    code = ''
    for stmt in stmts:
        code += stmt.get_code()
    return code


def incremental_computation(old_code: str, new_code: str) -> List[str]:
    """

    :param old_code:
    :param new_code:
    :return:
    """
    incremental_stmts = list()
    new_module = grammar.parse(new_code)
    old_graph = simple_dependency(old_code)
    recalculation_usage = dict()
    code_lines = parso.split_lines(new_code, keepends=True)
    module_context = ModuleValue(inference_state, new_module, code_lines).as_context()
    for stmt in new_module.children:

        if stmt.type != 'simple_stmt':
            continue

        leaves = get_leaves_of_node(stmt)
        leaf = leaves[0]

        need_recalculate = False
        if leaf.value in old_graph:
            deps = leaves[2:]
            if len(deps) != len(old_graph[leaf.value]):
                need_recalculate = True
            for i in range(len(deps)):
                if deps[i].value != old_graph[leaf.value][i].value or deps[i].type != old_graph[leaf.value][i].type:
                    need_recalculate = True
                    break
                if deps[i].type == 'name' and (deps[i].line, deps[i].column) in recalculation_usage:
                    need_recalculate = True
                    break

        else:
            need_recalculate = True

        if need_recalculate:
            rs = get_usage(module_context, leaf, inference_state)
            if len(rs) > 1:
                for r in rs[1:]:
                    line, column = r.line, r.column
                    recalculation_usage[(line, column)] = leaf

            incremental_stmts.append(stmt)
    code = get_codes(incremental_stmts)
    return code


def parallel_computation(code: str) -> List[str]:
    """

    :param code:
    :return:
    """
    module = grammar.parse(code)
    code_lines = parso.split_lines(code, keepends=True)
    module_context = ModuleValue(inference_state, module, code_lines).as_context()
    stmts: List[PythonNode] = list(filter(lambda x: x.type == 'simple_stmt', module.children))
    new_stmts = []
    stmts_order = []
    stmts_group_index = []
    group_count = 0
    group_index = 0
    for i in range(len(stmts)):
        stmt = stmts[i]
        try:
            index = new_stmts.index(stmt)
            group_index = stmts_group_index[index]
        except ValueError:
            new_stmts.append(stmt)
            stmts_order.append(stmt.start_pos[0])
            group_index = group_count
            stmts_group_index.append(group_index)
            group_count += 1
        finally:
            leaves = get_leaves_of_node(stmt)
            name_node = leaves[0]
            rs = get_usage(module_context, name_node, inference_state)
            if len(rs) > 1:
                for r in rs[1:]:
                    r: Leaf = module.get_leaf_for_position((r.line, r.column))
                    while r.type != 'simple_stmt':
                        r = r.parent
                    new_stmts.append(r)
                    stmts_order.append(r.start_pos[0])
                    stmts_group_index.append(group_index)
    zipped_stmts = list(zip(new_stmts, stmts_order, stmts_group_index))
    grouped_stmts = [[i[0:2] for i in zipped_stmts if i[2] == g] for g in range(group_count)]
    for i in range(group_count):
        grouped_stmts[i] = list(map(lambda x: x[0], sorted(grouped_stmts[i], key=lambda x: x[1])))
    codes = [get_codes(stmt) for stmt in grouped_stmts]
    return codes
