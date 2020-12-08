import jedi

code = """A = GET_SERIES('299013764')
B = LOG_CHANGE(
    A
)[1:2]
"""

code2 = """A = GET_SERIES('299013764')
B = LOG_CHANGE(A)
C = GET_SERIES('299013764')
"""

old_code = """A = GET('299013764','FIXINGS')
"""
new_code = """A = GET('299013764','FIXINGS')
B=GET('AAPL.OQ|RIC')
"""

if __name__ == '__main__':
    s = jedi.Script(code2)
    s.get_references(line=1, column=0)
