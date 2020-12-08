import parso
from parso.tree import NodeOrLeaf
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


def get_leaves_of_node(n: NodeOrLeaf):
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


def get_usage(context: ModuleContext, node: NodeOrLeaf, state: InferenceState):
    names = find_references(context, node, True)

    definitions = [classes.Name(state, n) for n in names]
    definitions = [d for d in definitions if not d.in_builtin_module()]
    return helpers.sorted_definitions(definitions)


def incremental_computation(old_code: str, new_code: str) -> List[PythonNode]:
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
    return incremental_stmts
