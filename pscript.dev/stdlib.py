"""
PScript standard functions.

Functions are declared as ... functions. Methods are written as methods
(using this), but declared as functions, and then "apply()-ed" to the
instance of interest. Declaring methods on Object is a bad idea (breaks
Bokeh, jquery).

"""

import re

# Functions not covered by this lib:
# isinstance, issubclass, print, max, min, callable, chr, ord

FUNCTIONS = {}
METHODS = {}
FUNCTION_PREFIX = '_pyfunc_'
METHOD_PREFIX = '_pymeth_'
CLASSES = {}
#CLASSES_PREFIX = 'PyClass_'
CLASSES_PREFIX = '' # XXX TODO much better
PYEXCEPTIONS = ('Exception', 'AssertionError', 'AttributeError', 'KeyError', 'ValueError', 'IndexError')

def get_std_info(code):
    """ Given the JS code for a std function or method, determine the
    number of arguments, function_deps and method_deps.
    """
    _, _, nargs = code.splitlines()[0].partition('nargs:')
    nargs = [int(i.strip()) for i in nargs.strip().replace(',', ' ').split(' ') if i]
    # Collect dependencies on other funcs/methods
    sep = FUNCTION_PREFIX
    function_deps = [part.split('(')[0].strip() for part in code.split(sep)[1:]]
    sep = METHOD_PREFIX
    method_deps = [part.split('.')[0].strip() for part in code.split(sep)[1:]]
    # Reduce and sort
    function_deps = sorted(set(function_deps))
    method_deps = sorted(set(method_deps))
    # Filter
    function_deps = [dep for dep in function_deps if dep not in method_deps]
    function_deps = set([dep for dep in function_deps if dep in FUNCTIONS])
    method_deps = set([dep for dep in method_deps if dep in METHODS])
    # Recurse
    for dep in list(function_deps):
        _update_deps(FUNCTIONS[dep], function_deps, method_deps)
    for dep in list(method_deps):
        _update_deps(METHODS[dep], function_deps, method_deps)

    return nargs, sorted(function_deps), sorted(method_deps)

def _update_deps(code, function_deps, method_deps):
    """ Given the code of a dependency, recursively resolve additional dependencies.
    """
    # Collect deps
    sep = FUNCTION_PREFIX
    new_function_deps = [part.split('(')[0].strip() for part in code.split(sep)[1:]]
    sep = METHOD_PREFIX
    new_method_deps = [part.split('.')[0].strip() for part in code.split(sep)[1:]]
    # Update
    new_function_deps = set(new_function_deps).difference(function_deps)
    new_method_deps = set(new_method_deps).difference(method_deps)
    function_deps.update(new_function_deps)
    method_deps.update(new_method_deps)
    # Recurse
    for dep in new_function_deps:
        _update_deps(FUNCTIONS[dep], function_deps, method_deps)
    for dep in new_method_deps:
        _update_deps(METHODS[dep], function_deps, method_deps)
    return function_deps, method_deps


def get_partial_std_lib(func_names, method_names, classes_names, indent=0,
                        func_prefix=None, method_prefix=None):
    """ Get the code for the PScript standard library consisting of
    the given function and method names. The given indent specifies how
    many sets of 4 spaces to prepend.
    """
    func_prefix = 'const ' + FUNCTION_PREFIX if (func_prefix is None) else func_prefix
    method_prefix = 'const ' + METHOD_PREFIX if (method_prefix is None) else method_prefix
    lines = []

    for l in PRECODE.strip().split('\n'):
        lines.append(l)
    #print('get_partial_std_lib:',func_names, 'method_names:', method_names, 'classes_names:', classes_names, 'indent:', indent)
    if classes_names:
        classes_names.add('Exception') # always used  TODO better
    for name in PYEXCEPTIONS:
        if name in classes_names:
          code = CLASSES[name].strip()
          lines.append(code)

    for name in sorted(func_names):
        code = FUNCTIONS[name].strip()
        if '\n' not in code:
            code = code.rsplit('//', 1)[0].rstrip()  # strip comment from one-liners
        lines.append('%s%s = %s;' % (func_prefix, name, code))
    for name in sorted(method_names):
        code = METHODS[name].strip()
        # lines.append('Object.prototype.%s%s = %s;' % (METHOD_PREFIX, name, code))
        lines.append('%s%s = %s;' % (method_prefix, name, code))
    code = '\n'.join(lines)
    if indent:
        lines = ['    '*indent + line for line in code.splitlines()]
        code = '\n'.join(lines)
    return code


def get_full_std_lib(indent=0):
    """ Get the code for the full PScript standard library.

    The given indent specifies how many sets of 4 spaces to prepend.
    If the full stdlib is made available in JavaScript, multiple
    snippets of code can be transpiled without inlined stdlib parts by
    using ``py2js(..., inline_stdlib=False)``.
    """
    return get_partial_std_lib(FUNCTIONS.keys(), METHODS.keys(), set(CLASSES.keys()), indent)


# todo: now that we have modules, we can have shorter/no prefixes, right?
# -> though maybe we use them for string replacement somewhere?
def get_all_std_names():
    """ Get list if function names and methods names in std lib.
    """
    return ([FUNCTION_PREFIX + f for f in FUNCTIONS],
            [METHOD_PREFIX + f for f in METHODS])


## ----- perhaps needed precode
PRECODE="""\
"""
## ----- Functions

## Special functions: not really in builtins, but important enough to support

FUNCTIONS['perf_counter'] = """function() { // nargs: 0
    if (typeof(process) === "undefined"){return performance.now()*1e-3;}
    else {const t = process.hrtime(); return t[0] + t[1]*1e-9;}
}"""  # Work in nodejs and browser

FUNCTIONS['time'] = """function () {return Date.now() / 1000;} // nargs: 0"""

## Hardcore functions
FUNCTIONS['op_instantiate_chk'] = """function (ob) { // nargs: 1
  return ((typeof ob === "undefined") ||
          (typeof window !== "undefined" && window === ob) ||
          (typeof global !== "undefined" && global === ob));
}"""

FUNCTIONS['op_instantiate'] = """function (ob, args) { // nargs: 2
    if ((typeof ob === "undefined") ||
        (typeof window !== "undefined" && window === ob) ||
        (typeof global !== "undefined" && global === ob))
        {throw "Class constructor is called as a function.";}
    for (let name in ob) {
        if (Object[name]===undefined) {
            const obj=ob[name];
            if (typeof obj==='function') {
                if (!obj.nobind) {
                   ob[name] = obj.bind(ob);
                   ob[name].__name__ = name;
                }
            } else if (obj !== null && obj !== undefined) {
                if (obj.__get__||obj.__set__) {
                   // print('name:', name, obj.__name__);
                   Object.defineProperty(ob, name, {
                      get:obj.__get__?function(){return obj.__get__(ob);}:undefined,
                      set:obj.__set__?function(v){obj.__set__(ob, v);}:undefined,
                   });
                }
            }
        }
    }
    if (ob.__init__) {
        ob.__init__.apply(ob, args);
    }
}"""

FUNCTIONS['create_dict'] = """function () {
    const d = {};
    for (let i=0; i<arguments.length; i+=2) { d[arguments[i]] = arguments[i+1]; }
    return d;
}"""

FUNCTIONS['merge_dicts'] = """function () {
    const res = {};
    for (let i=0; i<arguments.length; i++) {
        const d = arguments[i];
        const keys = Object.keys(d);
        for (let j=0; j<keys.length; j++) { const key = keys[j]; res[key] = d[key]; }
    }
    return res;
}"""

# args is a list of (name, default) tuples, and is overwritten with names from kwargs
FUNCTIONS['op_parse_kwargs'] = """
function (arg_names, arg_values, kwargs, strict) { // nargs: 3
    for (let i=0; i<arg_values.length; i++) {
        const name = arg_names[i];
        if (kwargs[name] !== undefined) {
            arg_values[i] = kwargs[name];
            delete kwargs[name];
        }
    }
    if (strict && Object.keys(kwargs).length > 0) {
        throw FUNCTION_PREFIXop_error('TypeError',
            'Function ' + strict + ' does not accept **kwargs.');
    }
    return kwargs;
}""".lstrip()


FUNCTIONS['op_error'] = """function (etype, msg) { // nargs: 2
    const e = new Error(etype + ': ' + msg);
    e.name = etype
    return e;
}"""

FUNCTIONS['hasattr'] = """function (ob, name) { // nargs: 2
    return (ob !== undefined) && (ob !== null) && (ob[name] !== undefined);
}"""

FUNCTIONS['getattr'] = """function (ob, name, deflt) { // nargs: 2 3
    const has_attr = ob !== undefined && ob !== null && ob[name] !== undefined;
    if (has_attr) {return ob[name];}
    else if (arguments.length == 3) {return deflt;}
    else {const e = new Error(name); e.name='AttributeError'; throw e;}
}"""

FUNCTIONS['setattr'] = """function (ob, name, value) {  // nargs: 3
    ob[name] = value;
}"""

FUNCTIONS['delattr'] = """function (ob, name) {  // nargs: 2
    delete ob[name];
}"""

FUNCTIONS['dict'] = """function (x) {
    const r={};
    if (Array.isArray(x)) {
        for (let i=0; i<x.length; i++) {
            const t=x[i]; r[t[0]] = t[1];
        }
    } else {
        const keys = Object.keys(x);
        for (let i=0; i<keys.length; i++) {
            const t=keys[i]; r[t] = x[t];
        }
    }
    return r;
}"""

FUNCTIONS['list'] = """function (x) {
    const r=[];
    if (typeof x==="object" && !Array.isArray(x)) {x = Object.keys(x)}
    for (let i=0; i<x.length; i++) {
        r.push(x[i]);
    }
    return r;
}"""

FUNCTIONS['set'] = """function (x) {
    const r = new Set();
    if (typeof x==="object" && !Array.isArray(x)) {x = Object.keys(x)}
    for (let i=0; i<x.length; i++) {
        r.add(x[i]);
    }
    return r;
}"""

FUNCTIONS['range'] = """function (start, end, step) {
    const res = [];
    let val = start;
    const n = (end - start) / step;
    for (let i=0; i<n; i++) {
        res.push(val);
        val += step;
    }
    return res;
}"""

#  console.log(str+'|'+arr);
FUNCTIONS['__sprintf'] = """function (tr,str, arr) {  // nargs: 3
  // code used from https://stackoverflow.com/a/13439711
  if (!str.length) {
    let sx = '';
    for (let i=0; i < arr.length; i++) {
      sx = sx + arr[i];
    }
    return sx;
  }
  var i = -1;
  function callback(pexp, p0, p1, p2, p3, p4) {
      // console.log('pexp|'+pexp+'|'+p4);
      if (pexp==='%%') return '%';
      if (pexp==='::') return ':';
      if (arr[++i]===undefined) return undefined;
      const exp  = p2 ? parseInt(p2.substr(1)) : undefined;
      const base = p3 ? parseInt(p3.substr(1)) : undefined;
      var val;
      switch (p4) {
          case 's': val = arr[i]; break;
          case 'c': val = arr[i][0]; break;
          case 'f':
          case 'F':
             val = parseFloat(arr[i]).toFixed(exp===undefined?6:exp);
             if (p4 === 'F') {val = val.toUpperCase();}
             break;
          case 'p':
          case 'g':
          case 'G':
             val = parseFloat(arr[i]).toPrecision(exp);
             if (p4 === 'G') {val = val.toUpperCase();}
             break;
          case 'e':
          case 'E':
             val = parseFloat(arr[i]).toExponential(exp===undefined?6:exp);
             if (val[val.length-2] == '+') { // +x -> +0x
               val = val.slice(0,-1) + '0' + val.slice(-1);
             }
             if (p4 === 'E') {val = val.toUpperCase();}
             break;
          case 'x':
          case 'X':
             val = parseInt(arr[i]).toString(base?base:16);
             if (p4 === 'X') {val = val.toUpperCase();}
             break;
          case 'o': val = parseInt(arr[i]).toString(8); break;
          case 'd':
          case 'i':
             val = parseFloat(parseInt(arr[i], base?base:10).toPrecision(exp)).toFixed(0);
             break;
      }
      val = typeof(val)==='object' ? JSON.stringify(val) : val.toString(base);
      var sz = parseInt(p1); /* padding size */
      var ch = p1 && p1[0]==='0' ? '0' : ' '; /* isnull? */
      while (val.length<sz) val = p0 !== undefined ? val+ch : ch+val; /* isminus? */
      return val;
  }
  // todo better ?
  const regex = tr==='%'?/%(-)?(0?[0-9]+)?([.][0-9]+)?([#][0-9]+)?([scfFpgGeExXodi%])/g
                        :/:(-)?(0?[0-9]+)?([.][0-9]+)?([#][0-9]+)?([scfFpgGeExXodi:])/g;
  return str.replace(regex, callback);
}"""

FUNCTIONS['_sprintf'] = """function (str, arr) {  // nargs: 2
  return FUNCTION_PREFIX__sprintf('%', str, arr);
}"""

FUNCTIONS['_sprintf2'] = """function (str, arr) {  // nargs: 2
  return FUNCTION_PREFIX__sprintf(':', str, arr);
}"""

# not really needed, but perhaps usefull for tests ?
# e.g. s = sprintf('%03d %03d', x, y)
FUNCTIONS['sprintf'] = """function (s) {  // nargs: -1
  const args = Array.prototype.slice.call(arguments, 1);
  return FUNCTION_PREFIX_sprintf(s, args);
}"""

# format uses ':'
FUNCTIONS['format'] = """function (v, fmt) {  // nargs: 2
  return FUNCTION_PREFIX_sprintf2(fmt, [v]);
}"""

# XXX perhaps enhance
FUNCTIONS['bytearray'] = """function (source) {  // nargs: 0 1
  if (source === undefined) return new Uint8Array();
  return Uint8Array.from(source);
}"""

## Normal functions

FUNCTIONS['pow'] = 'Math.pow // nargs: 2'

FUNCTIONS['sum'] = """function (x) {  // nargs: 1
    return x.reduce(function(a, b) {return a + b;});
}"""

# variants for round
# return Number(Number.parseFloat(x).toFixed(dec));
# return !dec ? Math.round(x) : Number(Number.parseFloat(x).toFixed(dec));
# better
# return (x >= 0) ? (!dec ? Math.round(x+Number.EPSILON) : Number(Math.round(x+Number.EPSILON+'e'+dec)+'e-'+dec))

FUNCTIONS['round'] = """function (x, dec) { // nargs: 1 2
  return (x >= 0) ? (!dec ? Math.round(x) : Number(Math.round(x+'e'+dec)+'e-'+dec))
                  : (!dec ? Math.round(x-Number.EPSILON) : Number(Math.round(x-Number.EPSILON+'e'+dec)+'e-'+dec));
}"""

FUNCTIONS['int'] = """function (x, base) { // nargs: 1 2
    if(base !== undefined) return parseInt(x, base);
    return x<0 ? Math.ceil(x): Math.floor(x);
}"""

FUNCTIONS['float'] = 'Number // nargs: 1'

FUNCTIONS['str'] = 'String // nargs: 0 1'

# Note use of "_IS_COMPONENT" to check for flexx.app component classes.
FUNCTIONS['repr'] = """function (x) { // nargs: 1
    var res; try { res = JSON.stringify(x); } catch (e) { res = undefined; }
    if (typeof res === 'undefined') { res = x._IS_COMPONENT ? x.id : String(x); }
    return res;
}"""

FUNCTIONS['bool'] = """function (x) { // nargs: 1
    return Boolean(FUNCTION_PREFIXtruthy(x));
}"""

FUNCTIONS['abs'] = 'Math.abs // nargs: 1'

FUNCTIONS['divmod'] = """function (x, y) { // nargs: 2
    const m = x % y; return [(x-m)/y, m];
}"""

FUNCTIONS['all'] = """function (x) { // nargs: 1
    for (let i=0; i<x.length; i++) {
        if (!FUNCTION_PREFIXtruthy(x[i])){return false;}
    } return true;
}"""

FUNCTIONS['any'] = """function (x) { // nargs: 1
    for (let i=0; i<x.length; i++) {
        if (FUNCTION_PREFIXtruthy(x[i])){return true;}
    } return false;
}"""

FUNCTIONS['enumerate'] = """function (iter) { // nargs: 1
    const res=[];
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    for (let i=0; i<iter.length; i++) {res.push([i, iter[i]]);}
    return res;
}"""

# TODO next should accept a default parameter
FUNCTIONS['next'] = """function (iter) { // nargs: 1
    return iter.next();
}"""

FUNCTIONS['zip'] = """function () { // nargs: 2 3 4 5 6 7 8 9
    const args = [];
    const res = [];
    let len = 1e20;
    for (let i=0; i<arguments.length; i++) {
        let arg = arguments[i];
        if ((typeof arg==="object") && (!Array.isArray(arg))) {arg = Object.keys(arg);}
        args.push(arg);
        len = Math.min(len, arg.length);
    }
    for (let j=0; j<len; j++) {
        const tup = []
        for (let i=0; i<args.length; i++) {tup.push(args[i][j]);}
        res.push(tup);
    }
    return res;
}"""

FUNCTIONS['reversed'] = """function (iter) { // nargs: 1
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    return iter.slice().reverse();
}"""

FUNCTIONS['sorted'] = """function (iter, key, reverse) { // nargs: 1 2 3
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    iter = iter.slice().sort(key?((a,b)=>key(a)-key(b)):((a,b)=>a -b));
    if (reverse) iter.reverse();
    return iter;
}"""

FUNCTIONS['filter'] = """function (func, iter) { // nargs: 2
    if (typeof func === "undefined" || func === null) {func = function(x) {return x;}}
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    return iter.filter(func);
}"""

FUNCTIONS['map'] = """function (func, iter) { // nargs: 2
    if (typeof func === "undefined" || func === null) {func = function(x) {return x;}}
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    return iter.map(func);
}"""

FUNCTIONS['len'] = """function (v) { // nargs: 1
    if (v instanceof Set || v instanceof Map) {return v.size;}
    if (v.length !== undefined) {return v.length;}
    return Object.keys(v).length; // e.g. for dict
}"""

## Other / Helper functions
#    // if ((!v) || typeof v === 'boolean' || typeof v === 'number') return v;
FUNCTIONS['truthy'] = """function (v) { // nargs: 1
    if (!v) return false;
    if (['boolean','number','string','function'].indexOf(typeof v) > -1) return v;
    if (v instanceof Set || v instanceof Map) return v.size ? v : false;
    if (v.length !== undefined) return v.length ? v : false;
    if (v.byteLength !== undefined) return v.byteLength ? v : false;
    return Object.keys(v).length ? v : false;
}"""

#     // console.log('a===b', a, b)
FUNCTIONS['op_equals'] = """function op_equals (a, b) { // nargs: 2
  if (a === b) {
     return true;
  }
  if (typeof a === 'number' || typeof a === 'string' || typeof a === 'boolean') {
    return false;
  }
  if (a&&b) {
     if (a instanceof Set) {
         if (a.size !== b.size) return false;
         for (let el of a) { if (!b.has(el)) return false; }
         return true;
     }
     if (a instanceof Map) {
         if (a.size !== b.size) return false;
         for (let el of a.keys()) if (!op_equals(a.get(el),b.get(el))) return false;
         return true;
     }
     if (Array.isArray(a) && Array.isArray(b)) {
         if (a.length !== b.length) return false;
         for (let i=0;i<a.length;i++) if (!op_equals(a[i], b[i])) return false;
         return true;
     }
     if (a instanceof Date) {
        return a == b;
     }
     if (a instanceof Object && b instanceof Object) {
         const akeys = Object.keys(a), bkeys = Object.keys(b);
         akeys.sort(); bkeys.sort();
         if (!op_equals(akeys,bkeys)) return false;
         for (let i of akeys) if (!op_equals(a[i],b[i])) return false;
         return true;
     }
  }
  return false;
}"""
    #console.log('op_contains:', b ? b.constructor : b);
FUNCTIONS['op_contains'] = """function op_contains (a, b) { // nargs: 2
    if (b == null) {
    } else if (b.constructor === Set) {
        return b.has(a);
    } else if (Array.isArray(b)) {
        for (let i=0; i<b.length; i++) {if (FUNCTION_PREFIXop_equals(a, b[i])) return true; }
        return false;
    } else if (b.constructor === Object) {
        for (let k in b) {if (a == k) return true;}
        return false;
    } else if (b.constructor === String) {
        return b.indexOf(a) >= 0;
    } else if (b.has !== undefined) { // like Set
        return b.has(a);
    } const e = Error('Not a container: ' + b); e.name='TypeError'; throw e;
}"""

FUNCTIONS['op_add'] = """function (a, b) { // nargs: 2
    if (Array.isArray(a) && Array.isArray(b)) {return a.concat(b);}
    if (a.constructor === Set && b.constructor === Set) {const u=new Set(a);for (let x of b) {u.add(x);} return u;}
    return a + b;
}"""

FUNCTIONS['op_mod'] = """function (a, b) { // nargs: 2
    if (a.constructor === String) {
      return FUNCTION_PREFIX__sprintf('%', a, b);
    }
    return a % b;
}"""


FUNCTIONS['op_mult'] = """function (a, b) { // nargs: 2
    if ((typeof a === 'number') + (typeof b === 'number') === 1) {
        if (a.constructor === String) return METHOD_PREFIXrepeat(a, b);
        if (b.constructor === String) return METHOD_PREFIXrepeat(b, a);
        if (Array.isArray(b)) {const t=a; a=b; b=t;}
        if (Array.isArray(a)) {
            let res = []; for (let i=0; i<b; i++) res = res.concat(a);
            return res;
        }
    } return a * b;
}"""


## ----- Methods

## List only

METHODS['append'] = """function (x) { // nargs: 1
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    this.push(x);
}"""

METHODS['extend'] = """function (x) { // nargs: 1
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    this.push.apply(this, x);
}"""

METHODS['insert'] = """function (i, x) { // nargs: 2
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    i = (i < 0) ? this.length + i : i;
    this.splice(i, 0, x);
}"""

METHODS['remove'] = """function (x) { // nargs: 1
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    for (let i=0; i<this.length; i++) {
        if (FUNCTION_PREFIXop_equals(this[i], x)) {this.splice(i, 1); return;}
    }
    const e = Error(x); e.name='ValueError'; throw e;
}"""

METHODS['reverse'] = """function () { // nargs: 0
    this.reverse();
}"""

METHODS['sort'] = """function (key, reverse) { // nargs: 0 1 2
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    this.sort(key?((a,b)=>key(a)-key(b)):((a,b)=>a -b));
    if (reverse) this.reverse();
}"""

## List and dict

METHODS['clear'] = """function () { // nargs: 0
    if (Array.isArray(this)) {
        this.splice(0, this.length);
    } else if (this.constructor === Object) {
        const keys = Object.keys(this);
        for (let i=0; i<keys.length; i++) delete this[keys[i]];
    } else return this.KEY.apply(this, arguments);
}"""

METHODS['copy'] = """function () { // nargs: 0
    if (Array.isArray(this)) {
        // return this.slice(0);
        return [...this]; // modern
    } else if (this.constructor === Object) {
        //var key, keys = Object.keys(this), res = {};
        //for (var i=0; i<keys.length; i++) {key = keys[i]; res[key] = this[key];}
        //return res;
        return {...this}; // modern
    } else return this.KEY.apply(this, arguments);
}"""

METHODS['pop'] = """function (i, d) { // nargs: 1 2
    if (Array.isArray(this)) {
        i = (i === undefined) ? -1 : i;
        i = (i < 0) ? (this.length + i) : i;
        const popped = this.splice(i, 1);
        if (popped.length)  return popped[0];
        const e = Error(i); e.name='IndexError'; throw e;
    } else if (this.constructor === Object) {
        const res = this[i]
        if (res !== undefined) {delete this[i]; return res;}
        else if (d !== undefined) return d;
        const e = Error(i); e.name='KeyError'; throw e;
    } else return this.KEY.apply(this, arguments);
}"""

## List and str

# start and stop not supported for list on Python, but for simplicity, we do
METHODS['count'] = """function (x, start, stop) { // nargs: 1 2 3
    start = (start === undefined) ? 0 : start;
    stop = (stop === undefined) ? this.length : stop;
    start = Math.max(0, ((start < 0) ? this.length + start : start));
    stop = Math.min(this.length, ((stop < 0) ? this.length + stop : stop));
    if (Array.isArray(this)) {
        let count = 0;
        for (let i=0; i<this.length; i++) {
            if (FUNCTION_PREFIXop_equals(this[i], x)) {count+=1;}
        } return count;
    } else if (this.constructor == String) {
        let count = 0;
        let i = start;
        while (i >= 0 && i < stop) {
            i = this.indexOf(x, i);
            if (i < 0) break;
            count += 1;
            i += Math.max(1, x.length);
        } return count;
    } else return this.KEY.apply(this, arguments);
}"""

METHODS['index'] = """function (x, start, stop) { // nargs: 1 2 3
    start = (start === undefined) ? 0 : start;
    stop = (stop === undefined) ? this.length : stop;
    start = Math.max(0, ((start < 0) ? this.length + start : start));
    stop = Math.min(this.length, ((stop < 0) ? this.length + stop : stop));
    if (Array.isArray(this)) {
        for (let i=start; i<stop; i++) {
            if (FUNCTION_PREFIXop_equals(this[i], x)) {return i;} // indexOf cant
        }
    } else if (this.constructor === String) {
        const i = this.slice(start, stop).indexOf(x);
        if (i >= 0) return i + start;
    } else return this.KEY.apply(this, arguments);
    const e = Error(x); e.name='ValueError'; throw e;
}"""

## Dict only

# note: fromkeys is a classmethod, and we dont support it.

METHODS['get'] = """function (key, d) { // nargs: 1 2
    if (this.constructor !== Object) return this.KEY.apply(this, arguments);
    if (this[key] !== undefined) {return this[key];}
    else if (d !== undefined) {return d;}
    else {return null;}
}"""

METHODS['items'] = """function () { // nargs: 0
    if (this.constructor !== Object) return this.KEY.apply(this, arguments);
    const keys = Object.keys(this);
    const res = [];
    for (let i=0; i<keys.length; i++) {const key = keys[i]; res.push([key, this[key]]);}
    return res;
}"""

METHODS['keys'] = """function () { // nargs: 0
    if (typeof this['KEY'] === 'function') return this.KEY.apply(this, arguments);
    return Object.keys(this);
}"""

METHODS['popitem'] = """function () { // nargs: 0
    if (this.constructor !== Object) return this.KEY.apply(this, arguments);
    const keys = Object.keys(this);
    if (keys.length == 0) {const e = Error(); e.name='KeyError'; throw e;}
    const key = keys[keys.length-1]; const val = this[key]; delete this[key];
    return [key, val];
}"""

METHODS['setdefault'] = """function (key, d) { // nargs: 1 2
    if (this.constructor !== Object) return this.KEY.apply(this, arguments);
    if (this[key] !== undefined) {return this[key];}
    else if (d !== undefined) { this[key] = d; return d;}
    else {return null;}
}"""

METHODS['update'] = """function (other) { // nargs: 1
    if (this.constructor !== Object) return this.KEY.apply(this, arguments);
    const keys = Object.keys(other);
    for (let i=0; i<keys.length; i++) {const key = keys[i]; this[key] = other[key];}
    return null;
}"""

METHODS['values'] = """function () { // nargs: 0
    if (this.constructor !== Object) return this.KEY.apply(this, arguments);
    const keys = Object.keys(this), res = [];
    for (let i=0; i<keys.length; i++) {const key = keys[i]; res.push(this[key]);}
    return res;
}"""

## String only

# ignores: encode, decode, format_map, isprintable, maketrans

# Not a Python method, but a method that we need, and is only ECMA 6
# http://stackoverflow.com/a/5450113/2271927
METHODS['repeat'] = """function(count) { // nargs: 0
    if (this.repeat) return this.repeat(count);
    if (count < 1) return '';
    let result = ''; let pattern = this.valueOf();
    while (count > 1) {
        if (count & 1) result += pattern;
        count >>= 1, pattern += pattern;
    }
    return result + pattern;
}"""

METHODS['capitalize'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return this.slice(0, 1).toUpperCase() + this.slice(1).toLowerCase();
}"""

METHODS['casefold'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return this.toLowerCase();
}"""

METHODS['center'] = """function (w, fill) { // nargs: 1 2
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    fill = (fill === undefined) ? ' ' : fill;
    const tofill = Math.max(0, w - this.length);
    const left = Math.ceil(tofill / 2);
    const right = tofill - left;
    return METHOD_PREFIXrepeat(fill, left) + this + METHOD_PREFIXrepeat(fill, right);
}"""

METHODS['endswith'] = """function (x) { // nargs: 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return this.lastIndexOf(x) == this.length - x.length;
}"""

METHODS['expandtabs'] = """function (tabsize) { // nargs: 0 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    tabsize = (tabsize === undefined) ? 8 : tabsize;
    return this.replace(/\\t/g, METHOD_PREFIXrepeat(' ', tabsize));
}"""

METHODS['find'] = """function (x, start, stop) { // nargs: 1 2 3
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    start = (start === undefined) ? 0 : start;
    stop = (stop === undefined) ? this.length : stop;
    start = Math.max(0, ((start < 0) ? this.length + start : start));
    stop = Math.min(this.length, ((stop < 0) ? this.length + stop : stop));
    const i = this.slice(start, stop).indexOf(x);
    if (i >= 0) return i + start;
    return -1;
}"""

METHODS['format'] = """function () {
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    const parts = [];
    let i = 0;
    let itemnr = -1;
    while (i < this.length) {
        // find opening
        const i1 = this.indexOf('{', i);
        if (i1 < 0 || i1 == this.length-1) { break; }
        if (this[i1+1] == '{') {parts.push(this.slice(i, i1+1)); i = i1 + 2; continue;}
        // find closing
        const i2 = this.indexOf('}', i1);
        if (i2 < 0) { break; }
        // parse
        itemnr += 1;
        const fmt = this.slice(i1+1, i2);
        let index = fmt.split(':')[0].split('!')[0];
        index = index? Number(index) : itemnr
        const s = FUNCTION_PREFIXformat(arguments[index], fmt);
        parts.push(this.slice(i, i1), s);
        i = i2 + 1;
    }
    parts.push(this.slice(i));
    return parts.join('');
}"""

METHODS['isalnum'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return Boolean(/^[A-Za-z0-9]+$/.test(this));
}"""

METHODS['isalpha'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return Boolean(/^[A-Za-z]+$/.test(this));
}"""

METHODS['isidentifier'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return Boolean(/^[A-Za-z_][A-Za-z0-9_]*$/.test(this));
}"""

METHODS['islower'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    const low = this.toLowerCase(), high = this.toUpperCase();
    return low != high && low == this;
}"""

METHODS['isdecimal'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return Boolean(/^[0-9]+$/.test(this));
}"""

# The thing about isdecimal, isdigit and isnumeric.
# https://stackoverflow.com/a/36800319/2271927
#
# * isdecimal() (Only Decimal Numbers)
# * str.isdigit() (Decimals, Subscripts, Superscripts)
# * isnumeric() (Digits, Vulgar Fractions, Subscripts, Superscripts,
#   Roman Numerals, Currency Numerators)
#
# In other words, isdecimal is the most strict. We used to have
# isnumeric with isdecimal's implementation, so we provide isnumeric
# and isdigit as aliases for now.

METHODS['isnumeric'] = METHODS['isdigit'] = METHODS['isdecimal']

METHODS['isspace'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return Boolean(/^\\s+$/.test(this));
}"""

METHODS['istitle'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    const low = this.toLowerCase(), title = METHOD_PREFIXtitle(this);
    return low != title && title == this;
}"""

METHODS['isupper'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    const low = this.toLowerCase(), high = this.toUpperCase();
    return low != high && high == this;
}"""

METHODS['join'] = """function (x) { // nargs: 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return x.join(this);  // call join on the list instead of the string.
}"""

METHODS['ljust'] = """function (w, fill) { // nargs: 1 2
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    fill = (fill === undefined) ? ' ' : fill;
    const tofill = Math.max(0, w - this.length);
    return this + METHOD_PREFIXrepeat(fill, tofill);
}"""

METHODS['lower'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return this.toLowerCase();
}"""

METHODS['lstrip'] = """function (chars) { // nargs: 0 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    chars = (chars === undefined) ? ' \\t\\r\\n' : chars;
    for (let i=0; i<this.length; i++) {
        if (chars.indexOf(this[i]) < 0) return this.slice(i);
    } return '';
}"""

METHODS['partition'] = """function (sep) { // nargs: 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    if (sep === '') {const e = Error('empty sep'); e.name='ValueError'; throw e;}
    const i1 = this.indexOf(sep);
    if (i1 < 0) return [this.slice(0), '', '']
    const i2 = i1 + sep.length;
    return [this.slice(0, i1), this.slice(i1, i2), this.slice(i2)];
}"""

METHODS['replace'] = """function (s1, s2, count) {  // nargs: 2 3
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    let i = 0;
    const parts = [];
    count = (count === undefined) ? 1e20 : count;
    while (count > 0) {
        const i2 = this.indexOf(s1, i);
        if (i2 >= 0) {
            parts.push(this.slice(i, i2));
            parts.push(s2);
            i = i2 + s1.length;
            count -= 1;
        } else break;
    }
    parts.push(this.slice(i));
    return parts.join('');
}"""

METHODS['rfind'] = """function (x, start, stop) { // nargs: 1 2 3
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    start = (start === undefined) ? 0 : start;
    stop = (stop === undefined) ? this.length : stop;
    start = Math.max(0, ((start < 0) ? this.length + start : start));
    stop = Math.min(this.length, ((stop < 0) ? this.length + stop : stop));
    const i = this.slice(start, stop).lastIndexOf(x);
    if (i >= 0) return i + start;
    return -1;
}"""

METHODS['rindex'] = """function (x, start, stop) {  // nargs: 1 2 3
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    const i = METHOD_PREFIXrfind(this, x, start, stop);
    if (i >= 0) return i;
    const e = Error(x); e.name='ValueError'; throw e;
}"""

METHODS['rjust'] = """function (w, fill) { // nargs: 1 2
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    fill = (fill === undefined) ? ' ' : fill;
    const tofill = Math.max(0, w - this.length);
    return METHOD_PREFIXrepeat(fill, tofill) + this;
}"""

METHODS['rpartition'] = """function (sep) { // nargs: 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    if (sep === '') {const e = Error('empty sep'); e.name='ValueError'; throw e;}
    const i1 = this.lastIndexOf(sep);
    if (i1 < 0) return ['', '', this.slice(0)]
    const i2 = i1 + sep.length;
    return [this.slice(0, i1), this.slice(i1, i2), this.slice(i2)];
}"""

METHODS['rsplit'] = """function (sep, count) { // nargs: 1 2
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    sep = (sep === undefined) ? /\\s/ : sep;
    count = Math.max(0, (count === undefined) ? 1e20 : count);
    const parts = this.split(sep);
    const limit = Math.max(0, parts.length-count);
    const res = parts.slice(limit);
    if (count < parts.length) res.splice(0, 0, parts.slice(0, limit).join(sep));
    return res;
}"""

METHODS['rstrip'] = """function (chars) { // nargs: 0 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    chars = (chars === undefined) ? ' \\t\\r\\n' : chars;
    for (let i=this.length-1; i>=0; i--) {
        if (chars.indexOf(this[i]) < 0) return this.slice(0, i+1);
    } return '';
}"""

METHODS['split'] = """function (sep, count) { // nargs: 0, 1 2
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    if (sep === '') {const e = Error('empty sep'); e.name='ValueError'; throw e;}
    sep = (sep === undefined) ? /\\s/ : sep;
    if (count === undefined) { return this.split(sep); }
    const res = [];
    let i = 0, index1 = 0;
    while (i < count && index1 < this.length) {
        const index2 = this.indexOf(sep, index1);
        if (index2 < 0) { break; }
        res.push(this.slice(index1, index2));
        index1 = index2 + sep.length || 1;
        i += 1;
    }
    res.push(this.slice(index1));
    return res;
}"""

METHODS['splitlines'] = """function (keepends) { // nargs: 0 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    keepends = keepends ? 1 : 0
    const finder = /\\r\\n|\\r|\\n/g;
    let i = 0;
    const parts = [];
    while (finder.exec(this) !== null) {
        const i2 = finder.lastIndex -1;
        const isrn = i2 > 0 && this[i2-1] == '\\r' && this[i2] == '\\n';
        if (keepends) parts.push(this.slice(i, finder.lastIndex));
        else parts.push(this.slice(i, i2 - isrn));
        i = finder.lastIndex;
    }
    if (i < this.length) parts.push(this.slice(i));
    else if (!parts.length) parts.push('');
    return parts;
}"""

METHODS['startswith'] = """function (x) { // nargs: 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return this.indexOf(x) == 0;
}"""

METHODS['strip'] = """function (chars) { // nargs: 0 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    chars = (chars === undefined) ? ' \\t\\r\\n' : chars;
    const s1 = this;
    let s2 = '', s3 = '';
    for (let i=0; i<s1.length; i++) {
        if (chars.indexOf(s1[i]) < 0) {s2 = s1.slice(i); break;}
    } for (let i=s2.length-1; i>=0; i--) {
        if (chars.indexOf(s2[i]) < 0) {s3 = s2.slice(0, i+1); break;}
    } return s3;
}"""

METHODS['swapcase'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    const res = [];
    for (let i=0; i<this.length; i++) {
        const c = this[i];
        if (c.toUpperCase() == c) res.push(c.toLowerCase());
        else res.push(c.toUpperCase());
    } return res.join('');
}"""

METHODS['title'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    const res = [], tester = /^[^A-Za-z]?[A-Za-z]$/;
    for (let i=0; i<this.length; i++) {
        const i0 = Math.max(0, i-1);
        if (tester.test(this.slice(i0, i+1))) res.push(this[i].toUpperCase());
        else res.push(this[i].toLowerCase());
    } return res.join('');
}"""

METHODS['translate'] = """function (table) { // nargs: 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    const res = [];
    for (let i=0; i<this.length; i++) {
        const c = table[this[i]];
        if (c === undefined) res.push(this[i]);
        else if (c !== null) res.push(c);
    } return res.join('');
}"""

METHODS['upper'] = """function () { // nargs: 0
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return this.toUpperCase();
}"""

METHODS['zfill'] = """function (width) { // nargs: 1
    if (this.constructor !== String) return this.KEY.apply(this, arguments);
    return METHOD_PREFIXrjust(this, width, '0');
}"""

# divers
# send to an iterator (generator)
METHODS['send'] = """function (value) { // nargs: 1
    if (this[Symbol.iterator] === undefined) return this.KEY.apply(this, arguments);
    let x = this.next(value);
    if (x.done === true) {
      return null; // TODO ?
    }
    return x.value;
}"""

for key in METHODS:
    METHODS[key] = re.subn(r'METHOD_PREFIX(.+?)\(',
                           r'METHOD_PREFIX\1.call(', METHODS[key])[0]
    METHODS[key] = METHODS[key].replace(
        'KEY', key).replace(
        'FUNCTION_PREFIX', FUNCTION_PREFIX).replace(
        'METHOD_PREFIX', METHOD_PREFIX).replace(
        ', )', ')')

for key in FUNCTIONS:
    FUNCTIONS[key] = re.subn(r'METHOD_PREFIX(.+?)\(',
                             r'METHOD_PREFIX\1.call(', FUNCTIONS[key])[0]
    FUNCTIONS[key] = FUNCTIONS[key].replace(
        'KEY', key).replace(
        'FUNCTION_PREFIX', FUNCTION_PREFIX).replace(
        'METHOD_PREFIX', METHOD_PREFIX)

#---------------------------------------------------
# XXX TODO better
def make_error_class(name):
    d = dict(
      proto = 'Error' if name == 'Exception' else CLASSES_PREFIX+'Exception',
      name = name,
      fullname = CLASSES_PREFIX+name,
      _ko_='{', _kc_='}',
    )

    code = []

    code.append("""\
function {fullname}(text){_ko_}
  const err = new {proto}('{name}'+text?text:'');
  err.name = '{name}';
  Object.setPropertyOf(err, Object.getPrototypeOf(this));
  return err;
{_kc_}

{fullname}.prototype = Object.create({proto}.prototype, {_ko_}
  constructor: {_ko_}
    value: {proto},
    enumerable: false,
    writable: true,
    configurable: true
  {_kc_}
{_kc_});

{name}.__proto__ = {proto};
""".format(**d))

    return '\n'.join(code)

for name in PYEXCEPTIONS:
    CLASSES[name] = make_error_class(name)

