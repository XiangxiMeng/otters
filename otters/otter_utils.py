from IPython.display import display, Markdown


def print_node_tree(node):
    s = [(node, 0)]
    while len(s) > 0:
        node, sep = s.pop()
        if hasattr(node, 'value'):
            print('  ' * sep, node.value)
        else:
            print('  ' * sep, node)
        if hasattr(node, 'children'):
            for n in reversed(node.children):
                s.append((n, sep + 1))


def lev_map(s, t, equal_func=lambda x, y: x == y):
    ls, lt = len(s), len(t)
    d = [[0] * (lt + 1) for i in range(ls + 1)]
    for i in range(1, ls + 1):
        d[i][0] = i
    for j in range(1, lt + 1):
        d[0][j] = j
    for j in range(1, lt + 1):
        for i in range(1, ls + 1):
            sub_cost = 0 if equal_func(s[i - 1], t[j - 1]) else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + sub_cost)
    return d


def mark_map(s, t, equal_func=lambda x, y: x == y):
    g = lev_map(s, t, equal_func)
    ls, lt = len(s), len(t)
    new_t = []
    while ls >= 1 and lt >= 1:
        #         make ls-1, lt-1 first to minimize
        x, y, o = min([(ls - 1, lt - 1, 0), (ls, lt - 1, 1), (ls - 1, lt, -1)], key=lambda p: g[p[0]][p[1]])
        if g[x][y] == g[ls][lt]:
            new_t.append((t[y], None))
            ls, lt = x, y
            continue
        if o == -1:
            new_t.append((s[x], o))
        elif o == 0:
            new_t.append((t[y], o))
        else:
            new_t.append((t[y], o))
        ls, lt = x, y
    return list(reversed(new_t))


def print_c(s, color: int):
    if color is None:
        display(Markdown(s))
    else:
        c = ['red', 'blue', 'green']
        display(Markdown(f"<span style='color:{c[color + 1]}'>{s}</span>"))
