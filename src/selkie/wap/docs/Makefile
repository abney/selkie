
DOCS =		$(HOME)/.cache/cld
HERE =		$(PWD)
PKGNAME =	pd2
DOCS =		$(PD)/docs
SRC =		$(PD)/src/$(PKGNAME)

DOCFILES =	index.html __main__.py pyodide default.css
PKGFILES =	Makefile pyproject.toml README.rst setup.cfg
SRCFILES =	__init__.py bar.py doc.py

all:	$(PD) $(PKGFILES:%=$(PD)/%) \
	$(DOCS) $(DOCFILES:%=$(DOCS)/%) \
	$(SRC) $(SRCFILES:%=$(SRC)/%)
	cd $(PD); make

$(PD) $(DOCS) $(SRC):
	mkdir -p $@

$(PD)/Makefile:	inst-makefile
	cp -p $< $@

$(PD)/%:	$(HERE)/%
	ln -s $< $@

$(DOCS)/pyodide:
	cd $(DOCS); tar xfy $(HOME)/tar/cl/src/2024/pyodide-0.26.1.tar.bz2

$(DOCS)/default.css:	$(HOME)/git/hub/selkie/src/selkie/cld/lib/default.css
	cp -p $< $@

$(DOCS)/%:	./docs/%
	cp -p $< $@

$(SRC)/%:	./src/%
	cp -p $< $@
