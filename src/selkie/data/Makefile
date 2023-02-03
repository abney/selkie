
include ../../CONFIG

D =		$(DEST)/python/nell/data

MODULES =	\
	__init__ \
	tblex \
	brown \
	census \
	panlex


all:	$D $(MODULES:%=$D/%.py)

$D:
	mkdir -p $@

$D/%:	%
	cp -p $< $@
