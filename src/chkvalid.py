# Copyright (c) 2020-present, pyxdroid MIT License
#
# Some validation checks, examples and benchmarks for testing python transpilers.
#
# Mainly made for develop version of PScript, but may be usefull for other transpilers e.g. Transcrypt too.
#
# The transpiled .js file should run with qjs (quickjs) or nodejs
# nodejs is much faster, but sometimes only qjs will work better.
# All examples run with native python3 and should be tested with it first.
#
# if False#
# This file contains some pre-processor (prepare) statemenents to integrate some constructs
# which are not allowed to all tested transpilers.
# These pre-processor statements are: #if cond#, #else# and #endif#.
# The stripped pre-processor line must start with '#' and end with '#'
# The defines are set in the prepare script.
# endif#
#
# some examples / comments are taken from the original flexx PScript transpiler (docs)
# https://github.com/flexxui/pscript
# PScript compiler is:
# Copyright (c) 2016-2020, Almar Klein
# Distributed under the (new) BSD License.
#
#
# example script for PScript:
#
# ./pyxc -q chkvalid.py || ./pyxc -j chkvalid.py
#
# ---------------------------------------------------------------------
# example for transcrypt
# for use with qjs (node probably not working)
#
# transcrypt -n -k -g -i -t chkvalid.py && qjs __target__/chkvalid.js
#
#
# =================================================================================
#
# these 'constants' are set/interpreted by the transpiler and not by the prepare script
IS_PY = False  # standard Python
IS_PS = False  # PScript
IS_TC = False  # Transcrypt

# force setting the constants
# if IS_PS#
IS_PS = True   # pyscript
#endif#

# if IS_PY#
IS_PY = True  # standard Python
#endif#

# if IS_TC#
IS_TC = True  # transcrypt
#endif#


# if USE_IMPORT#
from time import time
# else#


def time():
    return Date.now() / 1000.0
# endif#


#__pragma__ ('skip')
# this code is skipped in Transcrypt
IS_TC = False  # definitiv no Transcrypt

# dummy for not Transcrypt


def __new__(x): return x

#__pragma__ ('noskip')


# only one line should be printed here
if IS_PY:
    print('Referenz Python')
if IS_PS:
    print('PScript Transpiler')
if IS_TC:
    print('Transcrypt Transpiler')

#if IS_PY#
if IS_PY:
    # used for real python only
    #__pragma__ ('skip')
    # must be skipped by Transcrypt, because Transcrypt wants to export variable 'Map' here
    class Map():  # Python do not have Map, cheap emulation here
        def __init__(self, **args):
            self._d = dict(**args)

        def set(self, x, y): self._d[x] = y
        def get(self, k): return self._d.get(k)
        def entries(self): return self._d.items()
        def items(self): return self._d.items()
        def keys(self): return self._d.keys()
        def values(self): return self._d.values()

        def __iter__(self):
            return iter(self._d.items())
    #__pragma__ ('noskip')
#endif #
# -------------------------------------------------------------------------------------


def truefalsy1(checker):
    cke = checker.expect_equal
    cktrue = checker.expect_true
    ckfalse = checker.expect_false

    a = [0]
    b = []
    c = {}
    d = {0: 0}
    cktrue([0], '[0]')
    ckfalse([], '[]')
    ckfalse({}, '{}')
    ckfalse(c, 'c({})')
    cktrue({0: 0}, '{0:0}')
    cktrue(d, 'd({0: 0})')
    cktrue(d == {0: 0}, 'd == {0:0}')
    cktrue(c == {}, 'c == {}')

# if USE_SET#
    ckfalse(set(), 'set()')
    cktrue(set([0]), 'set([0])')
    cktrue({47}, '{47}')
# else#
    print('NO USE_SET')
# endif#
    cktrue(a == [0], 'a == [0]')
    cktrue(b == [], 'b == []')
    cktrue(b or a, 'b or a')
    cktrue(a or b, 'a or b')
    ckfalse(b and a, 'b and a')
    ckfalse(a and b, 'a and b')
    cktrue(True, 'True')
    ckfalse(False, 'False')
    ckfalse(None, 'None')
    ckfalse(0, '0')
    ckfalse('', '""')
    cktrue(1, '1')
    cktrue('0', '"0"')


def truefalsy2(checker):
    cke = checker.expect_equal
    cktrue = checker.expect_true
    ckfalse = checker.expect_false

    def f(): pass
    cktrue(f, 'function')
    ckfalse(f(), 'function()->None')

    x = 0
    cke(x or 0, 0, "x(0) or 0")
    cke(1 and x, False, "1 and x(0)")
    cke(x and 1, False, "x(0) and 1")

    x = 1
    cke(x or 0, 1, "x(1) or 0")
    cke(x or 2, 1, "x(1) or 2")
    cke(2 or x, 2, "2 or x(1)")
    cke(2 and x, 1, "2 and x(1)")

    a = []
    a = a or [1]  # a is now [1]
    cke(a, [1], "a is now [1]")
    b = [2] or a  # is [2]
    cke(b, [2], "b is now [2]")


def truefalsy3(checker):
    cke = checker.expect_equal
    cktrue = checker.expect_true
    ckfalse = checker.expect_false
    call = checker.call
    if not IS_PY:
        # real python do not have undefined
        call(lambda: ckfalse(undefined, 'undefined'), 'undefined')

        def f():
            x = undefined
            ckfalse(x, 'x(undefined)')
        call(f, 'x(undefined)')


def basics1(checker):
    cke = checker.expect_equal
    ckr = checker.expect_range
    cktrue = checker.expect_true
    ckfalse = checker.expect_false
    ckl = checker.expect_result

    # Simple operations
    cke(3 + 4 - 1, 6)
    cke(3 * 7 / 9, 2.3333333333333335, '3*7/9')
    cke(5**2, 25)
    cke(pow(5, 2), 25)
    cke(7 // 2, 3, '7//2')

    # Lists and dicts
    foo = [1, 2, 3]
    cke(foo, [1, 2, 3])
    cke(foo, list((1, 2, 3)))
    cke(len(foo), 3)
    cke(foo[2], 3)
    cke(foo[0], 1)

    bar = {'a': 1, 'b': 2}
    cke(len(bar), 2, "len(bar)")
    cke(bar['b'], 2)

    # Slicing lists
    foo = [1, 2, 3, 4, 5]
    cke(len(foo), 5)
    cke(foo[2:], [3, 4, 5], 'slice')
    cke(foo[2:-2], [3], 'slice')

    a = [1, 2, 3, 4]
    a[1] = 12

    # if USE_LEFT_HAND_SLICE#
    def _f():
        a[2:4] = [22, 33]
        return a
    ckl(_f, [1, 12, 22, 33], 'left-hand slice')
    # endif#

    # Slicing strings
    bar = 'abcdefghij'
    cke(len(bar), 10)
    cke(bar[2:], 'cdefghij')
    cke(bar[2:-2], 'cdefgh')

    # Subscripting
    foo = {'bar': 3}
    cke(len(foo), 1, "len(foo)")
    cke(foo['bar'], 3)
    # foo.bar  # Works in PScript (JS), but not in Python

    # some more simple basics
    a = 1, 2, 3
    a1, a2, a3 = a
    cke(a[0], a1, "cmp a[0] a1")
    cke(a[0], 1, "cmp a[0] 1")
    cke(a2, 2)
    del a   # in PScript a 'delete a;a=undefinded;delete a' is made
    # this do not work in PScript, because no Exception is raised here
    try:
        b = a
    except:
        b = 'Exc:del'
    cke(b, 'Exc:del', 'access to deleted var',
        'will probably never work in PScript')  # differs undefined vs null

    d = {'a': '11'}
    cke(len(d), 1, "len dict with one entry")
    del d['a']
    cke(len(d), 0, "len dict with deleted entry")

    cke(chr(65), 'A', 'chr(65)')
    cke(ord('A'), 65, "ord('A')")

    d = dict([['foo', 1], ['bar', 2]])  # -> {'foo': 1, 'bar': 2}
    l = list('abc')  # -> ['a', 'b', 'c']
    cke(d, {'foo': 1, 'bar': 2}, "dict")
    cke(l, ['a', 'b', 'c'], "list")
    d2 = dict(d)
    l2 = list(l)
    cke((d2, l2), (d, l), "dict + list copy")

    #
    # some simple math, results from python3
    #
    cke(round(1.33333), 1, 'round one param')

    # if USE_ROUND2#
    cke(round(1.33333, 0), 1, 'round1')
    cke(round(1.33333), 1, 'round1(1')
    cke(round(1.33333, 2), 1.33, 'round2')
    ckr(round(1.005, 2), [1, 1.01], 'round3')  # 1.01 is more precise
    cke(round(1.005001, 2), 1.01, 'round3(1')
    cke(round(1.455, 2), 1.46, 'round4')
    cke(round(-1.455, 2), -1.46, 'round5')
    cke(round(-1.455001, 2), -1.46, 'round5')
    cke(round(1.3549999999999998, 2), 1.35, 'round6')
    cke(round(14.45, 0), 14, 'round7')
    cke(round(14.49, 0), 14, 'round8')
    ckr(round(14.5, 0), [14, 15], 'round9')  # 15 is more precise
    cke(round(14.5001, 0), 15, 'round9(1')
    ckr(round(2.675, 2), [2.67, 2.68], 'round10')  # 2.68 is more precise
    cke(round(2.675001, 2), 2.68, 'round10(1')
    # else#
    print('NO USE_ROUND2')
    # endif#

    #
    cke(int(1.33333), 1, 'int1')
    cke(int(1.9), 1, 'int2')
    cke(int(1.0), 1, 'int3')
    #
    cke(abs(344.5 * 22 * -1) * -2, -15158, 'abs')
    #
    cke(divmod(100, 7), (14, 2), 'divmod')
    #
    # instances

    # Basic types
    ckfalse(isinstance(3, float), 'isinstance(3,float)',
            'in JS there are no ints')
    # cktrue(isinstance(3, int))  # in JS there are no ints
    cktrue(isinstance(3.0, float), 'isinstance float')
    cktrue(isinstance('', str))
    cktrue(isinstance([], list))
    cktrue(isinstance({}, dict))


def basics2(checker):
    cke = checker.expect_equal
    ckr = checker.expect_range
    cktrue = checker.expect_true
    ckfalse = checker.expect_false
    ckl = checker.expect_result

    def foo(): return 'x'
    if not IS_PY:
        cktrue(isinstance(foo, types.FunctionType), 'FunctionType')

        # Can also use JS strings
        cktrue(isinstance(3, 'number'))
        cktrue(isinstance('', 'string'))
        cktrue(isinstance([], 'array'))
        cktrue(isinstance({}, 'object'))
        cktrue(isinstance(foo, 'function'))

    class MyClass:
        pass

    class B(MyClass):
        pass

    # You can use it on your own types too ...
    x = B()
    cktrue(isinstance(x, MyClass), 'isinstance MyClass')
    if IS_PS:
        # special in pscript
        cktrue(isinstance(x, 'MyClass'))  # equivalent
        # also yields true (subclass of Object)
        cktrue(isinstance(x, 'Object'))

    # issubclass works too
    cktrue(issubclass(B, MyClass), 'issubclass MyClass')

    # As well as callable
    cktrue(callable(foo), 'callable(foo)')
    ckfalse(callable(x), 'callable(x)')

    # hasattr, getattr, setattr and delattr
    # -------------------------------------
    a = {'foo': 1, 'bar': 2}

    if IS_PS:
        # do not work with python3
        cktrue(hasattr(a, 'foo'), 'hasattr1')
        cke(getattr(a, 'foo'), 1, 'getattr1')

    ckfalse(hasattr(a, 'fooo'), 'hasattr2')
    ckfalse(hasattr(None, 'foo'), 'hasattr3')

    checker.expect_exception(lambda: getattr(
        a, 'fooo'), AttributeError, 'getattr2')

    cke(getattr(a, 'fooo', 3), 3, 'getattr3')

    checker.expect_result(lambda: getattr(None, 'foo', 3), 3, 'getattr4')

    if IS_PS:
        # do not work with python3
        setattr(a, 'foo', 2)
        cke(getattr(a, 'foo'), 2, 'getattr5')
        delattr(a, 'foo')
        ckfalse(hasattr(a, 'foo'), 'hasattr4')

    # ------------------
    # Creating sequences
    # ------------------
    cke(list(range(5)), [0, 1, 2, 3, 4], 'range1')
    cke(list(range(2, 10, 2)), [2, 4, 6, 8], 'range2')
    cke(list(range(100, 95, -1)), [100, 99, 98, 97, 96], 'range3')
    foo = [1, 9, 8, 2]
    bar = ['a', 'b', 'c']
    cke(list(reversed(foo)), [2, 8, 9, 1], 'reversed')
    cke(list(sorted(foo)), [1, 2, 8, 9], 'sorted')
    cke(list(enumerate(foo)), [(0, 1), (1, 9), (2, 8), (3, 2)], 'enumerate')
    cke(list(zip(foo, bar)), [(1, 'a'), (9, 'b'), (8, 'c')], 'zip')
    cke(list(filter(lambda x: x in [2, 3, 9], foo)), [9, 2], 'filter')
    cke(list(map(lambda x: x + 1, foo)), [2, 10, 9, 3], 'map')
    foo.append(10)
    cke(list(sorted(foo)), [1, 2, 8, 9, 10], 'sorted2')
    foo.remove(8)
    cke(list(sorted(foo)), [1, 2, 9, 10], 'sorted3')

    # ------------------
    # if statements
    # ------------------
    res = 0
    for val in range(10):
        if val > 7:
            result = 42
        elif val > 5:
            result = 1
        else:
            # One-line if
            result = 33 if val == 6 else 0
        res += result
    cke(res, 86, 'if-statements')

    # ------------------
    # looping
    # ------------------
    val = 0
    while val < 10:
        val += 1
    cke(val, 10, 'while loop')

    # Explicit iterating over arrays (and strings):
    val = 0
    for i in range(10):
        val += i

    for i in range(100, 10, -2):
        val += i

    # One way to iterate over an array
    arr = [1, 3, 8, 9]
    for i in range(len(arr)):
        val += arr[i]

    # But this is equally valid (and fast)
    for element in arr:
        val += element
    cke(val, 2607, 'iterations')

    # Iterations over dicts:

    result = 0
    d = {1: 44, 2: 55, 3: 88}

    # Plain iteration over a dict has a minor overhead
    for key in d:
        result += int(key)  # a dict key is always string in JS !!

    # Which is why we recommend using keys(), values(), or items()
    for key in d.keys():
        result += int(key)  # a dict key is always string in JS !!

    for val in d.values():
        result += val

    for key, val in d.items():
        result += int(key)    # a dict key is always string in JS !!
        result += val

    # if USE_ITER1#
    for kv in d.items():
        result += int(kv[0])    # a dict key is always string in JS !!
        result += int(kv[1])

    cke(result, 585, 'iterate over dict')
    # else#
    print('NO USE_ITER1')
    # endif#

    # Strings
    result = ''
    for char in "foo bar":
        result += char

    # More complex data structes
    for i, j in [[1, 2], [3, 4]]:
        result += str(i + j)

    cke(result, 'foo bar37', 'iterate strings/complex')

    # Builtin functions intended for iterations are supported too:
    foo = [1, 2, 3, 4]
    bar = [8, 9, 10, 11]
    result = 0

    for i, x in enumerate(foo):
        result += i
        result += x

    for a, b in zip(foo, bar):
        result += a
        result += b

    for x in reversed(sorted(foo)):
        result += x

    for x in map(lambda x: x + 1, foo):
        result += x

    for x in filter(lambda x: x > 0, foo):
        result += x

    cke(result, 98, 'builtin functions for iterate')

    # using set
    s1 = set([1, 2, 3, 5, 7, 1, 2, 3, 6])
    result = 0
    for x in s1:   # aware not sorted in JS
        # print(x)
        result += x
    cke(result, 24, 'set iterate')

    # using Map (JS)
    # a Map is similar to a dict in python but
    # iteration over object ist same as entries() or items() not keys()
    if IS_TC:
        m1 = __new__(Map())
    else:
        m1 = Map()
    # print(m1)
    m1.set(1, 4)
    m1.set(2, 6)

    result = 0
    for x in m1:  # like items() not keys() !!!!
        result += x[0]
        result += x[1]
    cke(result, 13, 'Map iterate direct')

    result = 0
    # works too
    for k, v in m1:
        result += k
        result += v
    cke(result, 13, 'Map iterate direct 2 targets')

    result = 0
    for x in m1.entries():  # like items()
        result += x[0]
        result += x[1]
    cke(result, 13, 'Map iterate entries')

    if not IS_TC:
        # special for PScript
        # not a real error in TC
        result = 0
        for k, v in m1.items():  # like real dict
            result += k
            result += v
        cke(result, 13, 'Map iterate items 2 targets')

        # if USE_ITER1#
        result = 0
        for x in m1.items():  # like entries()
            result += x[0]
            result += x[1]
        cke(result, 13, 'Map iterate items 1 target')
        # endif#

    # ------------------
    # Comprehensions
    # ------------------

    # List comprehensions just work
    x = [i * 2 for i in foo if i > 0]
    y = [i * j for i in [9, 10] for j in bar]
    cke(x + y, [2, 4, 6, 8, 72, 81, 90, 99, 80,
                90, 100, 110], 'list comprehensions')


def functions1(checker):
    cke = checker.expect_equal
    ckr = checker.expect_range
    ckl = checker.expect_result
    cktrue = checker.expect_true
    ckfalse = checker.expect_false

    def f1(*args):
        x = 0
        for c in args:
            x += c
        return x

    def f2(a, b, *args):
        x = a + b
        for c in args:
            x += c
        return x

    def f3(**kwargs):
        x = kwargs.get('e', 99)
        x += kwargs.get('f', 77)
        return x

    def f4(*args, **kwargs):
        x = kwargs.get('e', 99)
        x += kwargs.get('f', 77)
        for c in args:
            x += c
        return x

    def f5(a, b, *args, **kwargs):
        x = a + b
        x += kwargs.get('e', 99)
        x += kwargs.get('f', 77)
        for c in args:
            x += c
        return x

    result = f1(1, 2, 3, 4)
    result += f2(1, 2, 3, 4)
    cke(result, 20, 'f1 f2')

    result = f3(e=11, g=22, h=33)
    cke(result, 88, 'f3')

    result = f3(e=11, g=22, h=33)
    result += f4(1, 2, 3, 4, e=11, g=22, h=33)
    cke(result, 186, 'f3 f4')

    result = f5(1, 2, 3, 4, e=11, g=22, h=33)
    result += f5(1, 2, 3, 4, 5, 6, 7, 8, e=11, g=22, h=33)
    cke(result, 222, 'f5')

    # lambda
    def foo(x): return x**2
    ckl(lambda: foo(4), 16, 'lambda')

    foo = 10

    def fx(f1=f1, foo=foo, bar=20):  # simple in python, quirks in js
        return f1(foo + bar)

    ckl(lambda: fx(), 30, 'js quirks:fx() named params')


def functions2(checker):
    cke = checker.expect_equal
    cktrue = checker.expect_true
    ckfalse = checker.expect_false

    def is_prime(n):
        s = ['x']
        for i in range(2, n):
            # this must be done for transcrypt
            #__pragma__ ('opov')
            s += ['y'] * 2
            s += 2 * ['z']
            #__pragma__ ('noopov')
            if n % i == 0:
                return []
        if n > 1 and len(s) != 1 + 4 * (n - 2):
            raise ValueError('expected:%s, got:%s, hint:%s' %
                             (1 + 4 * (n - 2), len(s), n))
        return s if n > 1 else []

    def fib(n):
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    def primetest1(checker):
        cke = checker.expect_equal
        #
        primes = 0
        for n in range(100):
            if is_prime(n):
                primes += 1
        a = [fib(primes)]
        b = []
        cke(len(a), 1, 'primetest1-1')
        cke(a[0], 75025, 'primetest1-2')
        return a, b

    a, b = checker.call(primetest1)
    cke(len(b), 0, 'primetest1, len(b)')
    cktrue(a, 'primetest1, array')
    ckfalse(b, 'primetest1, empty array')

# if USE_YIELD#


def generators1(checker):
    cke = checker.expect_equal

    def gen1():
        for i in range(10):
            yield i

    result = 0
    for n in gen1():
        result += n
    cke(result, 45, 'gen1')


def generators2(checker):
    cke = checker.expect_equal

    def run_yield1():
        total = 0.0
        counter = 0
        average = None
        while True:
            term = yield average
            total += term
            counter += 1
            average = total / counter

    ra = run_yield1()  # initialize the generator
    next(ra)  # start the generator
    result = 0
    for value in [7, 13, 17, 231, 12, 8, 3]:
        avg = ra.send(value)
        result += avg
        #print(value, avg)
    cke(result, 241.90476190476193, 'yield1')


# else#
print('NO USE_YIELD')
# endif#


def classes(checker):
    cke = checker.expect_equal
    ckr = checker.expect_range
    cktrue = checker.expect_true
    ckfalse = checker.expect_false
    ckl = checker.expect_result

    class X:
        def __new__(cls, *args, **kwargs):
            #print('new1:', cls, 'args:', args, 'kwargs:', kwargs)
            x = super().__new__(cls)
            #print('new2:', str(x))
            return x

        def __init__(self, *args, **kwargs):
            #print('init', args, kwargs)
            self._prop1 = 47

# if USE_PROPERTY#
        # @property
        # def prop1(self):
        #  return self._prop1

        @classmethod
        def f(cls, *args):
            print('f:', cls, 'args:', args)

        # @classmethod
        # def f2(*args):
        #  print('f2','args:', args)

        @staticmethod
        def create():
            print('create:')

        @staticmethod
        def create2(param):
            print('create2:', param)

    x = X()
    x.create()
    X.create()
    x.create2('param1')
# else#
    print('NO USE_PROPERTY')
# endif#

    class A:
        def __init__(self, p1, p2):
            self.p1 = p1
            self.p2 = p2

        def sum(self):
            return self.p1 + self.p2 + self.p3 + self.p4

    class B(A):
        def __init__(self, p3, p4):
            A.__init__(self, 1, 2)
            self.p3 = p3
            self.p4 = p4

    ckl(lambda: B(3, 4).sum(), 10, 'subclass __init__')


def js_only(checker):
    # will only work with JS (transpiler)
    cke = checker.expect_equal
    ckr = checker.expect_range
    cktrue = checker.expect_true
    ckfalse = checker.expect_false

    if IS_TC:
        d1 = __new__(Date(2014))
        d2 = __new__(Date(2015))
    else:
        d1 = Date(2014)
        d2 = Date(2015)

    def get_utc():
        return time()

    utc = get_utc()

    cktrue(d2 > d1, 'js_only1')
    cktrue(d1 < d2, 'js_only2')
    cktrue(d1 != d2, 'js_only3')
    ckfalse(d1 == d2, 'js_only4')
    cktrue(d1 == d1, 'js_only5')
    cktrue(get_utc() - utc >= 0, 'js_only6')
    ckr(int(get_utc()) - int(utc), [0, 1], 'js_only7')


def strformat(checker):
    cke = checker.expect_equal
    # string formatting
    val = 42.2
    name = 'maier'
    cke("value: %g" % val, 'value: 42.2', 'ft1')
    cke("%s: %0.2f" % (name, val), 'maier: 42.20', 'ft2')

    cke("value: {:g}".format(val), 'value: 42.2', 'ft3')
    cke("{}: {:3.2f}".format(name, val), 'maier: 42.20', 'ft4')

    # F-strings (python 3.6+) not yet done
    # f"value: {val:g}"
    # f"{name}: {val:3.2f}"

    # This works
    t = "value: {:g}"
    cke(t.format(val), 'value: 42.2', 'ft5')

    # But this does not. PScript cannot know whether t is str or float and
    # the second operand is also unknown.
    # Therefore PScript will not insert a runtime modulo check here.
    t = "value: %g"
    cke(t % val, 'value: 42.2', 'ft6', 'will probably never work in PScript')

    # this works, because second operand is a tuple now.
    t = "value: %g"
    cke(t % (val,), 'value: 42.2', 'ft7')

    # and this too
    t = "value: %g %s"
    cke(t % (val, 'xx'), 'value: 42.2 xx', 'ft8')

    # some more formattings
    cke('%10s' % (name), '     maier', '%10s')
    cke('%04d' % (47), '0047', '%04d')
    cke('%04d-%02d-%02d %02d:%02d:%02d' %
        (800, 9, 3, 9, 4, 3), '0800-09-03 09:04:03')
    cke('%s' % (name), 'maier')
    cke('%0s:' % (name), 'maier:')
    cke('%0s:' % (''), ':')
    cke('%s:' % ('yyyy'), 'yyyy:')
    cke('%s::' % ('yyyy'), 'yyyy::')

    # %% also works as expected now
    cke('%s:::%s:::%s %%' % ('yyyy', name, 33), 'yyyy:::maier:::33 %')

    # if USE_STRFORMAT1#
    cke('%s:::%%sx' % ('yyyy'), 'yyyy:::%sx')
    cke('%s:::%%sx%s' % ('yyyy', name), 'yyyy:::%sxmaier')
    # else#
    print('NO USE_STRFORMAT1')
    # endif#

    # TypeError in Python, but compile error in PScript (probably better here ?)
    # try:
    #  cke('%s:::%%sx%s'%('yyyy'), 'yyyy:::%sx')
    # except TypeError:
    #  pass

    k = len('123')

    s = '%02d %04d %012d %2.3f %9.3g %g' % (5, 11, k, k, 47.33, 999.999)
    cke(s, '05 0011 000000000003 3.000      47.3 999.999', 'more strings 1')

    s = '{:02d} {:04d} {:012d} {:2.3f} {:9.3g} {:g} {:o} {:x} {:X}'.format(
        5, 11, k, k, 47.33, 999.999, 8888, 255, 127)
    cke(s, '05 0011 000000000003 3.000      47.3 999.999 21270 ff 7F', 'more strings 2')

    s = '{:g} {:G} {:f} {:F}'.format(1.2, 1.2, 1.2, 1.2)
    cke(s, '1.2 1.2 1.200000 1.200000', 'more strings 3')

    s = '{:e} {:E} {:e} {:e}'.format(1.2, 1.2, 2e9, 2e11)
    cke(s, '1.200000e+00 1.200000E+00 2.000000e+09 2.000000e+11', 'more strings 4')

    s = '%e %E %e %e' % (1.2, 1.2, 2e9, 2e11)
    cke(s, '1.200000e+00 1.200000E+00 2.000000e+09 2.000000e+11', 'more strings 5')


# ----------------------------------------
# if CHKPERF#
# if USE_LEFT_HAND_SLICE#
# include fannkuch.py#
# else#
print('NO FANNKUCH')
# endif#
# if USE_PYSTONE#
# include pystone.py#
# else#
print('NO USE_PYSTONE')
# endif#
# if USE_RICHARDS#
# include richards.py#
# else#
print('NO USE_RICHARDS')
# endif#


def bench_it(func, *args):
    start_time = time()
    result = func(*args)
    return time() - start_time, result


def chkperf(checker):
    cke = checker.expect_equal

    # if USE_PYSTONE#
    #if CHKPERF > 1#
    loops = 200000
    #else#
    loops = 50000
    #endif#
    benchtime, stones = pystones(loops)
    print('chkperf:pystones, loops:', loops,
          'benchtime:', benchtime, 'stones:', stones)
    # endif#

    # if USE_LEFT_HAND_SLICE#
    OK = {
        7: 228,
        8: 1616,
        9: 8629,
        10: 73196,
    }
    #if CHKPERF > 1#
    loops = 10
    #else#
    loops = 9
    #endif#

    benchtime, (count, checksum) = bench_it(fannkuch, loops)
    print('chkperf:fannkuch(' + str(loops) + ')',
          'benchtime:', benchtime, 'count:', count)
    cke(checksum, OK[loops], 'fannkuch')
    # endif#
    # if USE_RICHARDS#
    #if CHKPERF > 1#
    loops = 20
    #else#
    loops = 10
    #endif#
    r = Richards()
    benchtime, result = bench_it(r.run, loops)
    print('chkperf:richards(' + str(loops) + ')',
          'benchtime:', benchtime, 'result:', result)
    cke(result, True, 'richards')
    # endif#
#endif#

# if USE_IMPORT#


def imports(checker):
    # needs much more works in pscript
    # if not IS_TC#
    from plib import m2
    m2.tests(checker)
    # else#
    #from plib import m2
    # m2.tests(checker)
    # ^^ do not work in tc !? ^^
    # endif#
    from plib import m1
    m1.tests(checker)
    m1.f1('xx', 22, 33)
    from plib.m1 import f1
    f1('xx', 22, 33)
# endif#


def main(checker):
    checker.title = 'chkvalid'
    try:
        checker.call(truefalsy1, "truefalsy1")
        checker.call(truefalsy2, "truefalsy2")
        checker.call(truefalsy3, "truefalsy3")
        checker.call(basics1, "basics1")
        checker.call(basics2, "basics2")
        checker.call(functions1, "functions1")
        checker.call(functions2, "functions2")
        # if USE_YIELD#
        checker.call(generators1, "generators1")
        checker.call(generators2, "generators2")
        # endif#
        checker.call(classes, "classes")
        # if USE_IMPORT#
        checker.call(imports, "imports")
        # endif#

        if IS_TC:
            checker.add_warning(
                'strformat not checked because of too many errors')
        else:
            # to many errors in
            strformat(checker)

        if not IS_PY:
            js_only(checker)

        # if CHKPERF#
        checker.call(chkperf, "chkperf")
        # endif#

    except Exception as e:
        checker.add_error('Exception: ' + str(e))


def _main_():
    # if not USE_IMPORT#
    print('NO USE_IMPORT')
    # endif#

    # if not USE_EXCEPT_DEFAULT#
    print('NO USE_EXCEPT_DEFAULT')
    # endif#

    # if not USE_LEFT_HAND_SLICE#
    print('NO USE_LEFT_HAND_SLICE')
    # endif#

    class Checker:
        def __init__(self):
            self.title = ''
            self.expected = []
            self.errors = []
            self.warnings = []
            self.infos = []

        def expect_true(self, result, comment='', failed=''):
            self.add_expected(result and True or False, True, comment, failed)

        def expect_false(self, result, comment='', failed=''):
            self.add_expected(result and True or False, False, comment, failed)

        def expect_range(self, result, expected, comment='', failed=''):
            self.add_expected(result, expected, comment, failed, 'in')

        def expect_exception(self, func, Exc, comment='', failed=''):
            try:
                try:
                    func()
                    self.add_expected(None, str(Exc), comment, failed)
                except Exc:
                    self.add_expected(str(Exc), str(Exc), comment, failed)
            except Exception as e:
                self.add_expected('wrong Exc:' + str(e),
                                  str(Exc), comment, failed)

# if USE_EXCEPT_DEFAULT#
            except:
                print('unknown JS Exception in:', comment)
                self.add_expected('unknown JS Exception',
                                  str(Exc), comment, failed)
# endif#

        def expect_result(self, func, expexted, comment='', failed=''):
            try:
                res = func()
                self.add_expected(res, expexted, comment, failed)
            except Exception as e:
                self.add_expected('Exc:' + str(e), expexted, comment, failed)
# if USE_EXCEPT_DEFAULT#
            except:
                print('unknown JS Exception in:', comment)
                self.add_expected('unknown JS Exception',
                                  expexted, comment, failed)
# endif#

        def call(self, func, comment='', failed=''):
            try:
                return func(self)
            except Exception as e:
                self.add_expected(
                    'Exc:' + str(e), 'no exception', comment, failed)
# if USE_EXCEPT_DEFAULT#
            except:
                print('unknown JS Exception in:', comment)
                self.add_expected('unknown JS Exception',
                                  'no exception', comment, failed)
# endif#

        def expect_equal(self, result, expected, comment='', failed=''):
            self.add_expected(result, expected, comment, failed, '=')

        def add_expected(self, result, expected, comment='', failed='', op='='):
            self.expected.append((result, expected, comment, failed, op))

        def add_error(self, error):
            #print('add_error:', error)
            self.errors.append(error)

        def add_warning(self, warning):
            self.warnings.append(warning)

        def info(self, *args):
            a = []
            for p in args:
                a.append(p)
            self.infos.append(' '.join(a))

        def eval_results(self):
            print('EVAL ' + str(len(self.expected)) + ' results')
            for result, expected, comment, failed, op in self.expected:
                #print('eval_results:', result == expected, result, comment)
                if op == 'in':
                    ok = result in expected
                elif op == '=':
                    ok = result == expected
                else:
                    raise ValueError('wrong op:' + op)
                if not ok:
                    if failed:
                        # we know the failed, therefore a warning only
                        self.add_warning('result:' + str(result) + ', expected:' +
                                         str(expected) + ', "' + comment + '", ' + failed)
                    else:
                        # we do not know the failed, therefore an error here
                        self.add_error(
                            'result:' + str(result) + ', expected:' + str(expected) + ', "' + comment + '"')
            print('EVAL ' + str(len(self.errors)) + ' errors, ' +
                  str(len(self.warnings)) + ' warnings')

    checker = Checker()
    main(checker)
    checker.eval_results()
    if checker.errors:
        print('ERRORS -- ' + checker.title + ' -- ERRORS -----')
        for error in checker.errors:
            print(error)

    if checker.warnings:
        print('WARNING-- ' + checker.title + ' -- WARNING-----')
        for warning in checker.warnings:
            print(warning)

    if checker.infos:
        print('INFOS-- ' + checker.title + ' -- INFOS-----')
        for infos in checker.infos:
            print(info)


# if USE_HAS___NAME__#
if __name__ == '__main__':
    _main_()
#else#
print('NO USE_HAS___NAME__')
_main_()
# endif
