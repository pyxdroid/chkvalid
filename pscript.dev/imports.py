#mst:2020-02-15, simple imports
#code reused and extended from an older ?? flexx/pyscript version

IMPORT_PATHES = ['.','pyloc','pylib']
IMPORT_PREFIX = '_pyimp_'
IMPORT_DOT = '__'
IMPORTS = {}  # none (Modul) or code or tuple or dict  (s.b.)

def get_partial_import(imported_objects, imported_modules, indent, import_prefix=None):
    """ Get the code for imported modules """

    import_prefix = 'const ' + ( IMPORT_PREFIX if (import_prefix is None) else import_prefix )
    lines = []

    for name in sorted(imported_objects):
        if name in imported_modules:
          continue
        #print('get_partial_import object,name:'+name+':')
        if IMPORTS[name] is None:
            continue
        code = IMPORTS[name].strip()
        name = name.replace('.', IMPORT_DOT)
        lines.append('%s%s = %s;' % (import_prefix, name, code))

    for name in imported_modules:
        # NO sort here, the proper sequence is mandatory
        #print('get_partial_import modul,name:'+name+':')
        if IMPORTS[name] is None:
            continue
        code = IMPORTS[name].strip()
        name = name.replace('.', IMPORT_DOT)
        lines.append('%s%s = %s;' % (import_prefix, name, code))

    code = '\n' + '\n'.join(lines)
    if indent:
        lines = ['    '*indent + line for line in code.splitlines()]
        code = '\n'.join(lines)
    return code


import sys
IMPORTS['sys'] = None  # mark sys as a module
IMPORTS['sys.version_info'] = "[%s]" % ', '.join([str(x) for x in sys.version_info[:3]])
IMPORTS['sys.version'] = "'%s'" % ('.'.join([str(x) for x in sys.version_info[:3]]) + ' [PScript]')

# not very usefull for now
IMPORTS['sys.path'] = "[%s]" % ', '.join([ "'%s'"%(x) for x in IMPORT_PATHES])

IMPORTS['time'] = None  # mark time as a module
IMPORTS['time.perf_counter'] = """function() {
    if (typeof(process) === "undefined"){return performance.now()*1e-3;}
    else {const t = process.hrtime(); return t[0] + t[1]*1e-9;}
}"""  # Work in nodejs and browser

IMPORTS['time.clock'] = IMPORTS['time.perf_counter']
IMPORTS['time.process_time'] = IMPORTS['time.clock']
IMPORTS['time.time'] = """function () {return new Date().getTime() / 1000;}"""

#IMPORTS['time.strftime'] = """function () {
#IMPORTS['time.localtime'] = """function () {
#IMPORTS['time.gmtime'] = """function () {
#IMPORTS['time.mktime'] = """function () {

#IMPORTS['time.ctime'] = """function () {
#  return new Date().getTime() / 1000;
#}"""

#IMPORTS['time.struct_time'] = """function(y, m, d, hh, mm, ss, wday, dnum, dstflag) {
#  return { y, m, d, hh, mm, ss, wday, dnum, dstflag },
#    var msecs = secs * 1000, start = new Date();
#}"""


# should only be used in very rare cases/tests
IMPORTS['time.sleep'] = """function(secs) {
    var msecs = secs * 1000, start = new Date();
    while (new Date() - start < msecs) {}
}"""


# ========== some math and random staff mst:2020-02-15 ===============
IMPORTS['math'] = None # mark as module
IMPORTS['math.sin'] = ('F',"Math.sin")
IMPORTS['math.cos'] = ('F',"Math.cos")
IMPORTS['math.pi']  = ('C',"Math.PI")
IMPORTS['math.modf'] = """function (a){const i=Math.trunc(a); return [a-i, i];}"""

IMPORTS['random'] = None # mark as module
IMPORTS['random.random'] = ('F',"Math.random")
IMPORTS['random.randint'] = """function (a,b){return Math.floor(a + Math.random()*(b+1));}"""




