# simple Makefile for chkvalid
# Copyright (c) 2020-present pyxdroid MIT License
#

.PHONY: some all clean help ps pso p3 tc pep8

# ================ defaults may be overwritten by the lconfig file ============
#
# flags for the prepare program
# -v  for increment verbose level
# -Ddef for adding a define.
#   known defines are:
#     CHKPERF[=x] for enabling some perfomance checking code, higher x = longer
#

PREPFLAGS=-DCHKPERF=1

#
# flags for the pyxc program (for pscript(.dev))
# -v for verbose
# -q for run with qjs (QuickJS)
# -j for run with node(js)
# -t timed run (in combination with -q|-j)
#

PYXCFLAGS=-v -j -t

#
# path to the modified pscript
#
PSCRIPT_PS=pscript.dev

#
# path to the original pscript or empty if an installed pscript version is used
# e.g.  PSCRIPT_PSO=/u1/repos/pscript/pscript
#
PSCRIPT_PSO=

# flags for Transcrypt (see the Transcrypt documentation)
TRANSCRYPTFLAGS=-n -k -g -i -t

# run the transcrypt code
# probably do not run with node
TRANSCRYPTRUN=time qjs

# run the python3 compiler
PY3=time python3
# =============================================================================

# possibility to overwrite the defaults
-include ./lconfig

some: help p3 ps

help:
	@echo "===== help ============================================================"
	@echo "make: [ps | pso | tc | p3 | help | some | all | clean]"
	@echo "  ps:  develop version of pscript"
	@echo "  pso: original version of pscript (https://github.com/flexxui/pscript)"
	@echo "  tc:  Transcrypt (https://github.com/QQuick/Transcrypt)"
	@echo "  p3:  standard python3"
	@echo "some:  help p3 ps"
	@echo "======================================================================="
	@echo ""


all: p3 ps pso tc

lconfig: Makefile
	@touch lconfig

build/ps/chkvalid.py: src/chkvalid.py prepare lconfig src/plib/*.py
	./prepare $(PREPFLAGS) ps $< $@

build/pso/chkvalid.py: src/chkvalid.py prepare lconfig src/plib/*.py
	./prepare $(PREPFLAGS) pso $< $@

build/p3/chkvalid.py: src/chkvalid.py prepare lconfig src/plib/*.py
	./prepare $(PREPFLAGS) p3 $< $@

build/tc/chkvalid.py: src/chkvalid.py prepare lconfig src/plib/*.py
	./prepare $(PREPFLAGS) tc $< $@

ps: build/ps/chkvalid.py
	@echo "=== pscript.dev ======="
	./pyxc $(PYXCFLAGS) -S$(PSCRIPT_PS) -D$(dir $<) $(notdir $<)

pso: build/pso/chkvalid.py
	@echo "=== pscript original =="
	./pyxc $(PYXCFLAGS) -S$(PSCRIPT_PSO) -D$(dir $<) $(notdir $<)

p3: build/p3/chkvalid.py
	@echo "=== reference python ==="
	(cd $(dir $<) && $(PY3) $(notdir $<))

tc: build/tc/chkvalid.py
	@echo "=== Transcrypt ========"
	(cd $(dir $<) && transcrypt $(TRANSCRYPTFLAGS) $(notdir $<) && $(TRANSCRYPTRUN) __target__/$(notdir $(basename $<)).js)

clean:
        # remove prepared code
	-rm -rf build
        # and cache
	-rm -rf pscript.dev/__pycache__

pep8:
	autopep8 -i src/chkvalid.py
	autopep8 -i src/plib/*.py
	autopep8 -i prepare
	autopep8 -i pyxc


