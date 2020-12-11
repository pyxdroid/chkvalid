# -*- coding: utf-8
"""
Parts of this code (and in the other modules that define the parser
class) are inspired by / taken from the py2js project.

Useful links:
 * https://greentreesnakes.readthedocs.org/en/latest/nodes.html
 * https://github.com/qsnake/py2js/blob/master/py2js/__init__.py

Main limiting features for browsers (not sure if this is 100% complete):
* Object.keys supported from IE 9 - we use it in method_keys()

"""

import re
import sys
import json

from . import commonast as ast
from . import stdlib, logger
from . import imports

reprs = json.dumps  # Save string representation without the u in u'xx'.


class JSError(Exception):
    """ Exception raised when unable to convert Python to JS.
    """
    pass


def unify(x):
    """ Turn string or list of strings parts into string. Braces are
    placed around it if its not alphanumerical
    """
    # Note that r'[\.\w]' matches anyting in 'ab_01.äé'

    if isinstance(x, MantleCode):
        x = x.get_code_as_str()

    elif isinstance(x, (tuple, list)):
        x = ''.join(x)

    if x[0] in '\'"' and x[0] == x[-1] and x.count(x[0]) == 2:
        return x  # string
    elif re.match(r'^[\.\w]*$', x, re.UNICODE):
        return x  # words consisting of normal chars, numbers and dots
    elif re.match(r'^[\.\w]*\(.*\)$', x, re.UNICODE) and x.count(')') == 1:
        return x  # function calls (e.g. 'super()' or 'foo.bar(...)')
    elif re.match(r'^[\.\w]*\[.*\]$', x, re.UNICODE) and x.count(']') == 1:
        return x  # indexing
    elif re.match(r'^\{.*\}$', x, re.UNICODE) and x.count('}') == 1:
        return x  # dicts
    else:
        return '(%s)' % x


class NameSpace(dict):
    """ Representation of the namespace in a certain scope. It looks a bit like
    a set, but makes a distinction between used/defined and local/nonlocal.

    The value of an item in this dict can be:
    * 1: variable defined in this scope.
    * 2: nonlocal variable (set nonlocal in this scope).
    * 3: global variable (set global in this scope).
    * 4: global variable (set in a subscope).
    * set: variable used here (or in a subscope) but not defined here.
    """

    _pscript_overload = True
    _already_declared = None # optional set for already declared local vars in this scope

    def set_nonlocal(self, key):
        """ Explicitly declare a name as nonlocal """
        self[key] = 2  # also if already exists

    def set_global(self, key):
        """ Explicitly declare a name as global """
        self[key] = 3  # also if already exists
        # becomes 4 in parent scope

    def use(self, key, how):
        """ Declare a name as used and how (the full name.foo.bar). The name
        may be defined in higher level, or it will end up in vars_unknown.
        """
        hows = self.setdefault(key, set())
        #print('use:', key, how, hows)
        if isinstance(hows, set):
            hows.add(how)

    def add(self, key):
        """ Declare a name as defined in this namespace """
        # If value is 4, the name is used as a global in a subscope. At this
        # point, we do not know whether this is the toplevel scope (also
        # because py2js() is often used to transpile snippets which are later
        # combined), so we assume that the user know what (s)he is doing.
        curval = self.get(key, 0)
        if curval not in (2, 3):  # dont overwrite nonlocal or global
            self[key] = 1

    def discard(self, key):
        """ Discard name from this namespace """
        self.pop(key, None)

    def leak_stack(self, sub):
        """ Leak a child namespace into the current one. Undefined variables
        and nonlocals are moved upwards.
        """
        for name in sub.get_globals():
            sub.discard(name)
            if name not in self:
                self[name] = 4
            # elif self[name] not in (3, 4):  ... dont know whether outer scope
            #     raise JSError('Cannot use non-global that is global in subscope.')
        for name, hows in sub.get_undefined():
            sub.discard(name)
            for how in hows:
                self.use(name, how)

    def is_known(self, name):
        """ Get whether the given name is defined or declared global/nonlocal
        in this scope.
        """
        return self.get(name, 0) in (1, 2, 3)

    def get_defined(self):
        """ Get list of variable names that the current scope defines.
        """
        return set([name for name, val in self.items() if val == 1])

    def get_globals(self):
        """ Get list of variable names that are declared global in the
        current scope or its subscopes.
        """
        return set([name for name, val in self.items() if val in (3, 4)])

    def get_undefined(self):
        """ Get (name, set) tuples for variables that are used, but not
        defined. The set contains the ways in which the variable is used
        (e.g. name.foo.bar).
        """
        return [(name, val) for name, val in self.items() if isinstance(val, set)]

    def already_declared(self, name):
        return self._already_declared and name in self._already_declared

    def declare_var(self, name):
        if self._already_declared is None:
            self._already_declared = {name}
        else:
            self._already_declared.add(name)

class MantleCode(list):
    # mantle parsed code
    def __init__(self, parser, node, code=None, **kwargs):
        if code:
          list.__init__(self, code)
        self.parser = parser
        self.node = node
        self._kwargs = kwargs
        if not code:
           self += self.get_code()

    def __repr__(self):
        _sd = str(self._kwargs) if self._kwargs else ''
        _sl = list.__repr__(self) if len(self) else ''
        return 'MantleCode: %s %s %s'%(self.get_type(), _sd, _sl)

    def __getattr__(self, n):
        return self._kwargs[n]

    def get_type(self):
        return self.node.__class__.__name__ if self.node else None

    def get_code(self):
        return []

    def get_code_as_str(self):
        if len(self):
          # already code
          return ''.join(self)
        return ''.join(self.get_code())
        #return 'CodeMantle: %s %s'%(self.get_type(), self._kwargs)

    def assign(self, *args):
        return self.get_code_as_str() + " = " + ','.join(args)

class yyyyMantleCode(list):
    # mantle parsed code
    def __init__(self, code, type, **kwargs):
        if isinstance(code, tuple):
            code = list(code)
        if not isinstance(code, list):
            code = [code]
        self._code = code
        self._type = type
        self._kwargs = kwargs

    # make it compatible with String
    def __str__(self):
        return ''.join(self._code)

    def __add__(self, code):
        if isinstance(code, MantleCode):
            code = x._code

        if isinstance(code, tuple):
            code = list(code)

        if not isinstance(code, list):
            code = [code]
        self._code += code
        return self


class Parser0:
    """ The Base parser class. Implements the basic mechanism to allow
    parsing to work, but does not implement any parsing on its own.

    For details see the Parser class.
    """

    # Developer notes:
    # The parse_x() functions are called by parse() with the node of
    # type x. They should return a string or a list of strings. parse()
    # always returns a list of strings.

    NAME_MAP = {
        'True'  : 'true',
        'False' : 'false',
        'None'  : 'null',
        'unicode': 'str',  # legacy Py compat
        'unichr': 'chr',
        'xrange': 'range',
        'self': 'this',
    }

    ATTRIBUTE_MAP = {
        '__class__': 'Object.getPrototypeOf({})',
    }

    BINARY_OP = {
        'Add'    : '+',
        'Sub'    : '-',
        'Mult'   : '*',
        'Div'    : '/',
        'Mod'    : '%',
        'LShift' : '<<',
        'RShift' : '>>',
        'BitOr'  : '|',
        'BitXor' : '^',
        'BitAnd' : '&',
    }

    UNARY_OP = {
        'Invert' : '~',
        'Not'    : '!',
        'UAdd'   : '+',
        'USub'   : '-',
    }

    BOOL_OP = {
        'And'    : '&&',
        'Or'     : '||',
    }

    COMP_OP = {
        'Eq'    : "==",
        'NotEq' : "!=",
        'Lt'    : "<",
        'LtE'   : "<=",
        'Gt'    : ">",
        'GtE'   : ">=",
        'Is'    : "===",
        'IsNot' : "!==",
    }

    def __init__(self, code, pysource=None, indent=0, docstrings=True,
                 inline_stdlib=True, importmodule=None, insert_ipath=False, verbose=None):
        #print('Parser.__init__, inline_stdlib:', inline_stdlib, 'importmodule:', importmodule, insert_ipath)
        self._pycode = code  # helpfull during debugging
        self._pysource = None
        self._verbose = verbose or '#' # must be a char here because of in compares
        if isinstance(pysource, str):
            self._pysource = pysource, 0
        elif isinstance(pysource, tuple):
            self._pysource = str(pysource[0]), int(pysource[1])
        elif pysource is not None:
            logger.warning('Parser ignores pysource; it must be str or (str, int).')
        if sys.version_info[0] == 2:
            fut = 'from __future__ import unicode_literals, print_function\n'
            code = fut + code
        self._root = ast.parse(code)
        if sys.version_info[0] == 2:
            self._root.body_nodes.pop(0)  # remove that import node we added
        self._stack = []
        self._indent = indent
        self._dummy_counter = 0
        self._scope_prefix = []  # stack of name prefixes to simulate local scope

        # To keep track of std lib usage
        self._std_functions = set()
        self._std_methods = set()
        self._std_classes = set()

        self._imported_objects = set()
        self._imported_modules = []  # for proper sequence
        self._imports = {}
        flg_ipathes_inserted = False

        if self._pysource:
          import os
          _p = os.path.dirname(self._pysource[0])
          if _p:
            if importmodule:
              if insert_ipath:
                imports.IMPORT_PATHES.insert(0, _p)
                flg_ipathes_inserted = True
            else:
              imports.IMPORT_PATHES[0] = _p

        # To help distinguish classes from functions
        self._seen_func_names = set()
        self._seen_class_names = set()

        # Options
        self._docstrings = bool(docstrings)  # whether to inclue docstrings

        # Collect function and method handlers
        self._functions, self._methods = {}, {}
        for name in dir(self.__class__):
            if name.startswith('function_op_'):
                pass  # special operator function that we use explicitly
            elif name.startswith('function_'):
                self._functions[name[9:]] = getattr(self, name)
            elif name.startswith('method_'):
                self._methods[name[7:]] = getattr(self, name)

        self._classes = {}
        for v in stdlib.CLASSES.keys():
           self._classes[v] = ''

        # Prepare
        self.push_stack('module', importmodule or '')

        if importmodule:
          self._indent += 1

        # Parse
        try:
            self._parts = self.parse(self._root)
        except JSError as err:
            # Give smarter error message
            _, _, tb = sys.exc_info()
            try:
                msg = self._better_js_error(tb)
            except Exception:  # pragma: no cover
                raise(err)
            else:
                err.args = (msg + ':\n' + str(err), )
                raise(err)

        # Finish
        ns = self.vars  # do not self.pop_stack() so caller can inspect module vars
        defined_names = ns.get_defined()
        if defined_names:
            self._parts.insert(0, self.get_declarations(ns))

        # Add part of the stdlib that was actually used
        if inline_stdlib:
            libcode = imports.get_partial_import(self._imported_objects, self._imported_modules, self._indent)
            if libcode:
                self._parts.insert(0, libcode)

            libcode = stdlib.get_partial_std_lib(self._std_functions,
                                                 self._std_methods,
                                                 self._std_classes,
                                                 self._indent)
            if libcode:
                self._parts.insert(0, libcode)

        # Post-process
        if flg_ipathes_inserted:
          del imports.IMPORT_PATHES[0]

        if importmodule:
          # we are in a module
          #print('ns:', ns)
          self._indent -= 1
          # export all defined (value == 1) vars which do not start with '_'
          exports = [(name, value)[0] for name, value in sorted(ns.items()) if name[0] != '_' and value == 1]
          ##export_keyvals = [reprs(name) + ': ' + name for name in exports]
          code = self._parts
          code.insert(0,'(function(){ // imported python modul')
          ##code.append('\n    return {%s}; //exports\n' % ', '.join(export_keyvals))
          code.append('\n    return {%s}; //exports\n' % ', '.join(exports)) # we are modern :-)
          code.append('})()')
          self.exports = exports

        elif self._parts:
          self._parts[0] = '    ' * indent + self._parts[0].lstrip()

    def dump(self):
        """ Get the JS code as a string.
        """
        return ''.join(self._parts)

    def _better_js_error(self, tb):  # pragma: no cover
        """ If we get a JSError, we try to get the corresponding node
        and print the lineno as well as the function etc.
        """
        node = None
        classNode = None
        funcNode = None
        while tb.tb_next:
            tb = tb.tb_next
            node = tb.tb_frame.f_locals.get('node', node)
            classNode = node if isinstance(node, ast.ClassDef) else classNode
            funcNode = node if isinstance(node, ast.FunctionDef) else funcNode

        # Get location as accurately as we can
        filename = None
        lineno = getattr(node, 'lineno', -1)
        if self._pysource:
            filename, lineno = self._pysource
            lineno += node.lineno

        msg = 'Error processing %s-node' % (node.__class__.__name__)
        if classNode:
            msg += ' in class "%s"' % classNode.name
        if funcNode:
            msg += ' in function "%s"' % funcNode.name
        if filename:
            msg += ' in "%s"' % filename
        if hasattr(node, 'lineno'):
            msg += ', line %i, ' % lineno
        if hasattr(node, 'col_offset'):
            msg += 'col %i' % node.col_offset
        return msg

    def push_stack(self, type, name):
        """ New namespace stack. Match a call to this with a call to
        pop_stack() and process the resulting line to declare the used
        variables. type must be 'module', 'class' or 'function'.
        """
        assert type in ('module', 'class', 'function')
        #self._stack.append((type, name, NameSpace()))
        #mst:2020-06-11, use list for manipulation later, e.g. for yield
        self._stack.append([type, name, NameSpace()])

    def pop_stack(self):
        """ Pop the current stack and return the namespace.
        """
        # Pop
        nstype, nsname, ns = self._stack.pop(-1)
        self.vars.leak_stack(ns)
        return ns

    def get_declarations(self, ns):
        """ Get string with variable (and builtin-function) declarations.
        """
        if not ns:
            return ''
        code = []
        loose_vars = []
        for name, value in sorted(ns.items()):
            if value == 1:
                if not ns.already_declared(name):
                   loose_vars.append(name)
            # else: pass global/nonlocal or expected to be defined in outer scope
        if loose_vars:
            code.insert(0, self.lf('var %s;' % ', '.join(loose_vars)))
        return ''.join(code)

    def get_class_name(self):
        if self._stack:
            nstype, nsname, ns = self._stack[-1]
            if nstype == 'class':
                return nsname

    def get_class_property_code(self, varname, valuename, ro=False):
        ns = self.get_class_name()
        if not ns:
           raise JSError("logic error: not in class")
        code = []
        code.append(self.lf("Object.defineProperty(%s, '%s', {" % (ns, varname)) )
        code.append(self.lf('  get: function() { return %s; },' % (valuename)) )
        if not ro:
          code.append(self.lf('  set: function(v) { %s = v; },' % (valuename)) )
        code.append(self.lf('});'))
        return ''.join(code)

    def with_prefix(self, name, new=False):
        """ Add class prefix to a variable name if necessary.
        """
        nstype, nsname, ns = self._stack[-1]
        if nstype == 'class':
            if name.startswith('__') and not name.endswith('__'):
                name = '_' + nsname + name  # Double underscore name mangling
            return nsname + '.prototype.' + name
        else:
            return name

    @property
    def vars(self):
        """ NameSpace instance for the current stack. """
        return self._stack[-1][2]

    def lf(self, code=''):
        """ Line feed - create a new line with the correct indentation.
        """
        return '\n' + self._indent * '    ' + code

    def dummy(self, name='', tmp=False):
        """ Get a unique name. The name is added to vars.
        """
        self._dummy_counter += 1
        name = '_stub%i_%s' % (self._dummy_counter, name)
        if not tmp:
            self.vars.add(name)
        return name

    def _handle_std_deps(self, code):
        nargs, function_deps, method_deps = stdlib.get_std_info(code)
        for dep in function_deps:
            self._use_std_function(dep)
        for dep in method_deps:
            self.use_std_method('x', dep, [])

    def _use_std_function(self, name):
        """ Use a function from the PScript standard library.
        """
        self._handle_std_deps(stdlib.FUNCTIONS[name])
        self._std_functions.add(name)
        return stdlib.FUNCTION_PREFIX + name

    def use_std_function(self, name, arg_nodes):
        """ Use a function from the PScript standard library.
        """
        mangled_name = self._use_std_function(name)
        args = [(a if isinstance(a, str) else unify(self.parse(a)))
                for a in arg_nodes]
        return '%s(%s)' % (mangled_name, ', '.join(args))

    def use_std_method(self, base, name, arg_nodes):
        """ Use a method from the PScript standard library.
        """
        self._handle_std_deps(stdlib.METHODS[name])
        self._std_methods.add(name)
        mangled_name = stdlib.METHOD_PREFIX + name
        args = [(a if isinstance(a, str) else unify(self.parse(a)))
                for a in arg_nodes]
        #return '%s.%s(%s)' % (base, mangled_name, ', '.join(args))
        args.insert(0, base)
        return '%s.call(%s)' % (mangled_name, ', '.join(args))

    def use_std_class(self, name, arg_nodes=None):  # XXX TODO better
        """ Use a class from the PScript standard library. e.g. an exception
        """
        #print('use_std_class:', name, self._std_classes)
        self._std_classes.add(name)
        mangled_name = stdlib.CLASSES_PREFIX + name
        return mangled_name

    def use_imported_object(self, name, is_real_module=False):
        x = imports.IMPORTS[name]
        #print('use_imported_object:', name, x)

        # not a real import, more a macro
        if type(x) is tuple:
          if (x[0] in ('C', 'F')):
            return x[1]

        self._handle_std_deps(imports.IMPORTS[name])
        if is_real_module:
          # use list here for proper sequence
          self._imported_modules.append(name)
          return

        self._imported_objects.add(name)
        return imports.IMPORT_PREFIX + name.replace('.', imports.IMPORT_DOT)

    def pop_docstring(self, node):
        """ If a docstring is present, in the body of the given node,
        remove that string node and return it as a string, corrected
        for indentation and stripped. If no docstring is present return
        empty string.
        """
        docstring = ''
        if (node.body_nodes and isinstance(node.body_nodes[0], ast.Expr) and
                                isinstance(node.body_nodes[0].value_node, ast.Str)):
            docstring = node.body_nodes.pop(0).value_node.value.strip()
            lines = docstring.splitlines()
            getindent = lambda x: len(x) - len(x.strip())
            indent = min([getindent(x) for x in lines[1:]]) if (len(lines) > 1) else 0
            if lines:
                lines[0] = ' ' * indent + lines[0]
                lines = [line[indent:] for line in lines]
            docstring = '\n'.join(lines)
        return docstring

    def parse(self, node, **kwargs):
        """ Parse a node. Check node type and dispatch to one of the
        specific parse functions. Raises error if we cannot parse this
        type of node.

        Returns a list of strings.
        """
        nodeType = node.__class__.__name__
        parse_func = getattr(self, 'parse_' + nodeType, None)
        if parse_func:
            if self._verbose == 'X':
              print('parse_start:', node.lineno, nodeType, node.ctx, node)

            res = parse_func(node, **kwargs)
            if self._verbose == 'X':
              print('parse_end:', node.lineno, nodeType, res)

            if isinstance(res, MantleCode):
                return res # already mantled
            # Return as list also if a tuple or string was returned
            assert res is not None
            if isinstance(res, tuple):
                res = list(res)
            if not isinstance(res, list):
                res = [res]
            return MantleCode(self, node, res)
        else:
            raise JSError('Cannot parse %s-nodes yet' % nodeType)
