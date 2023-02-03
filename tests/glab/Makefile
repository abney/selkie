
TESTS =	01 02 03 04 05 06 07 08 09 10

test:	$(TESTS:%=test%.ok)

%.ok:	%.gn
	python -m seal.script.glab $< | diff $*.output -
	touch $@

clean:
	rm -f *.ok
