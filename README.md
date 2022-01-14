# Introduction

This tool may be used to validate a list of functions/results of a python transpiler.<br/>
The so far tested transpilers compile python code to js code.

## Beware
### It is more a GIST and WIP as a real package for now, but may already help transpiler developers/testers.
It is in use to develop and validate a local modified version of [pscript](https://github.com/flexxui/pscript).
This modified pscript version is included for tests as pscript.dev.<br/>
pscript.dev is used in some own projects for now.<br/>
See the ***pscript.dev/pyxdroid.txt*** file for some important modifications.<br/>
Some functions in pscript will always differ from real python. They are not marked as errors, but as warnings!<br/>
The code works under Unix. No efforts will be made to let it run under Win.<br/>
For testing pscript(.dev), the highest tested python3 version is ***3.9*** for now.

## Questions
Will probably answered lazy.

## Issues
Will probably fixed lazy.

## License

[MIT](http://opensource.org/licenses/MIT)

Copyright (c) 2020-present, pyxdroid

## General
The main checking code is in the src directory (chkvalid.py and others which might be included or imported).<br/>
With the help of the ***prepare*** script and a Makefile this code is prepared for the
different transpilers, compiled by the transpiler and run with [qjs](https://github.com/bellard/quickjs)
or node.js (see Makefile).<br/>
The ***prepare*** script also contains configuration data, which can be changed as needed.<br/>
An optional ***lconfig*** file may be used to overwrite default constants in the Makefile.

    # example optional lconfig, will be read by Makefile
    PREPFLAGS=
    PSCRIPT_PSO=/u1/repos/pscript/pscript

#### Beware: The performance highly depends on the js interpreter being used. (qjs or node)
The preparing is mainly a simple pre-processing of the src/chkvalid.py file.<br/>
The transpilers only support a subset of valid python code, therefore it is
necessary to exclude some valid python3 constructs.

The output of the prepare script is placed into the build/target directory.<br/>
The transpiler is started in this target directory as working directory and creates the target code.<br/>
The pscript transpilers are called by the ***pyxc*** script.

For using different versions of pscript the pyxc scripts may create a symbolic link to the
corresponding pscript version into the working (target) directory. This is controlled by the Makefile or lconfig constants:

     PSCRIPT_PS, PSCRIPT_PSO

For executing the resulting js code the programs [qjs](https://github.com/bellard/quickjs) and/or node.js must be installed.

Till now the following targets are provided/tested.

* p3: testing the code with standard python3 for reference (no js is created)
* ps: current develop version of pscript (included here as pscript.dev)
* pso: the original version of [pscript](https://github.com/flexxui/pscript)
* tc: using [Transcrypt](https://github.com/QQuick/Transcrypt) (not well supported! Needs qjs, do not work with node.js here!?)


Call:

    make [ ps|pso|tc|p3|help|some|all|clean ]

