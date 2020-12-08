import parso
from parso.tree import NodeOrLeaf
import jedi

grammar = parso.load_grammar(version='3.6')


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
    for simple_stmt in module.children:
        if simple_stmt.type != 'simple_stmt':
            continue
        leaves = get_leaves_of_node(simple_stmt)
        graph[leaves[0].value] = leaves[2:]
    return graph


def incremental_computation(old_code: str, new_code: str):
    incremental_stmts = list()
    new_module = grammar.parse(new_code)
    old_graph = simple_dependency(old_code)
    recalculation_usage = dict()
    script = jedi.Script(new_code)
    for simple_stmt in new_module.children:

        if simple_stmt.type != 'simple_stmt':
            continue

        leaves = get_leaves_of_node(simple_stmt)
        var = leaves[0]

        need_recalculate = False
        if var.value in old_graph:
            deps = leaves[2:]
            if len(deps) != len(old_graph[var.value]):
                need_recalculate = True
            for i in range(len(deps)):
                if deps[i].value != old_graph[var.value][i].value or deps[i].type != old_graph[var.value][i].type:
                    need_recalculate = True
                    break
                if deps[i].type == 'name' and (deps[i].line, deps[i].column) in recalculation_usage:
                    need_recalculate = True
                    break

        else:
            need_recalculate = True

        if need_recalculate:
            rs = script.get_references(line=var.line, column=var.column, scope='file')
            if len(rs) > 1:
                for r in rs[1:]:
                    line, column = r.line, r.column
                    recalculation_usage[(line, column)] = var

            incremental_stmts.append(simple_stmt)
    return incremental_stmts
