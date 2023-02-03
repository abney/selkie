
include ../CONFIG


E =		$(DEST)/examples
S =		$(PWD)

EXAMPLES =	$(shell cat EXAMPLES)

all:

install:	check_env install1

check_env:
	if [ -z "$(DEST)" ]; then echo "Not set: DEST" >&2; exit 1; fi
	if [ -z "$(EXAMPLES)" ]; then echo "Not set: EXAMPLES" >&2; exit 1; fi

install1:	$E $(EXAMPLES:%=$E/%)

$E:
	mkdir -p $@

$E/uc/.installed.1:
	if [ -e $E/uc ]; then chmod -R +w $E/uc; rm -rf $E/uc; fi
	tar cf - uc | (cd $E; tar xf -)
	touch $@

$E/corpus.cld:	corpus.cld
	tar cf - corpus.cld | (cd $E; tar xf -)

$E/%:	%
	cp $< $@

$E/%:	%.tgz
	cd $E; tar xfz $S/$*.tgz

uninstall:
	cd $E; rm -f $(EXAMPLES)

test:
	@echo "[35mTEST glab[39m"
	python -m seal.glab notebook_test.gl | diff - notebook_test.output
