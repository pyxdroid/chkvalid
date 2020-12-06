#mst:2020-02-16
import os
from . import Parser
from .imports import IMPORT_PATHES,IMPORT_DOT

namespace=None

def parse_module(parser, imports, fullname, modname):
  pycode = open(fullname, 'r').read() ## #.decode("utf-8")
  p = Parser(pycode, fullname, inline_stdlib = False, importmodule = modname, verbose=parser._verbose)
  jscode = p.dump()
  #print (fullname+':\n'+jscode+'\n'+str(p.exports))
  imports[modname] = jscode
  parser.use_imported_object(modname, True)
  for name in p.exports:
    imports[modname+'.'+name] = ('F','_pyimp_'+modname.replace('.',IMPORT_DOT) + '.' + name)
  # add to parent parser
  parser._std_functions |= p._std_functions
  parser._std_methods |= p._std_methods
  parser._std_classes |= p._std_classes
  parser._imported_objects |= p._imported_objects
  for m in p._imported_modules:
    if m not in parser._imported_modules:
      parser._imported_modules.insert(0, m)

def prepare(parser, imports, root, name):
  #print('importer,root:', root, 'name:', name, IMPORT_PATHES)

  if root:
    modname = root[:-1] # without '.'
  else:
    modname = name

  if modname in imports:
    return 'duplicate modul name:' + modname

  fnpa = modname.replace('.','/')
  fnpy = fnpa +'.py'

  fullname = None
  is_package = False

  for p in IMPORT_PATHES:
    for fn in (fnpy, fnpa):
      fullname = p + '/' + fn
      if not os.path.exists(fullname):
        #print('not exists:', os.path.realpath(fullname))
        fullname = None
      else:
        if fn[-3:] == '.py':
          break
        fup = fullname + '/__init__.py'
        if not os.path.exists(fup):
          #print('not exists:', os.path.realpath(fup))
          fullname = None
        else:
          is_package = True
          break
    if fullname:
      break

  if fullname is None:
    return 'import file not found:'+fn

  print('use import file/dir:', fullname)

  if is_package:
    imports[modname] = None # like module
    if root:
      fup = fullname + '/%s.py'%(name)
      if os.path.exists(fup):
        modname += ('.'+name)
        parse_module(parser, imports, fup, modname)

        #pycode = open(fup, 'r').read() ## #.decode("utf-8")
        #p = Parser(pycode, fup, inline_stdlib = False, importmodule = modname)
        #jscode = p.dump()
        ##print (jscode)
        #imports[modname] = jscode
        #parser.use_imported_object(modname, True)
        #for name in p.exports:
        #  imports[modname+'.'+name] = ('F','_pyimp_'+modname.replace('.',IMPORT_DOT) + '.' + name)
        #
    #for fn in os.listdir(fullname):
    #  if fn[-3:] == '.py' and fn[:-3] == name:
    #    print(fn)
    #    imports[modname][fn] = None

  else:
    parse_module(parser, imports, fullname, modname)

