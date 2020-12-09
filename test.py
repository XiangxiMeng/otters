from otters.sea_otter import incremental_computation, parallel_computation

old_code = """stock = 'aapl'
A = GET('299013764','FIXINGS')
B = GET(
    stock
    )
C = func(A,B)
D = new_func(A)
E = a_func(B,D)
"""

new_code = """A = GET('299013764','FIXINGS')
stock='t'
B=GET(stock)
D = new_func(A)
C = func(A,D)
"""

code = """A = GET('aapl')
B = GET('spx')
pa = func(A)
pb = func(B)
"""

if __name__ == '__main__':
    parallel_computation(code)
