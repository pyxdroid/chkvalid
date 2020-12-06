from .m1 import t1
from .m1 import tests as tests_m1
print('importing m2')


def m2_t1():
    return 'm2' + t1()


def tests(checker):
    cke = checker.expect_equal
    cke(t1(), 't1')
    cke(m2_t1(), 'm2t1')
    tests_m1(checker)
