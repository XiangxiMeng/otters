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

if __name__ == '__main__':
    from otters.sea_otter import incremental_computation
    stmts = incremental_computation(code, code2)
    stmts
