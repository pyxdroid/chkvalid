import sys
print('importing plib.m1, sys.version:', sys.version)


def f4(*args, **kwargs):
    k = len(args)
    d = kwargs['d1']
    return k * d


def f3(a, *args, **kwargs):
    k = len(args)
    d = kwargs['d1']
    return a


def f2(a, b, *args, **kwargs):
    k = len(args)
    d = kwargs['d1']
    a = f3(a, 1, d1=3)
    return a


def f1(x, y, z):
    d = y * z
    t = f2(d, 3, x, y, z, d1='data1', d2='data2')
    t = f3(d, 3, x, y, z, d1='data1', d2='data2')
    t = f4(d, 3, x, y, z, d1='data1', d2='data2')
    return x


def t1():
    return f1('t1', 2, 3)


def t2():
    return('t2')


def tests(checker):
    cke = checker.expect_equal
    ckr = checker.expect_range
    cktrue = checker.expect_true
    ckfalse = checker.expect_false
    ckl = checker.expect_result
    t111 = t1
    t22 = t2
    cke(t1(), 't1', 't1')
    cke(t22(), 't2', 't22')
