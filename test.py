import jedi

code = """A = GET_SERIES('299013764', 'FIXINGS')
B = LOG_CHANGE(A)
C = GET_SERIES('299013764', 'FIXINGS')
"""

if __name__ == '__main__':
    s = jedi.Script(code)
    s.get_references(line=1, column=0, scope='file')
    print(s._module_node)
    import parso
    parso.load_grammar()