def sum_evens(x):
    s = 0
    for i in x:
        if i % 2 == 0:
            s += i
    return s
