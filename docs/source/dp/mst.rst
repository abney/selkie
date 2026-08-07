
MST Parser — ``selkie.nlp.dp.mst``
**********************************

This is just a wrapper for the third-party MST dependency parser::

   >>> from selkie.nlp.dp.mst import mst
   >>> mst('spa')

The function mst() accepts the following optional arguments:

 * fmt — one of 'orig', 'uni', 'ch'.
   Default is 'orig'.

 * outfn — redirect stdout to this file.

 * space — the amount of memory to allocate, in GB.  Defaults
   to '5'.

The language name and format are passed to
seal.data.dep.datasets to retrieve the dataset for parsing.
Its 'train' and 'test' files are used.
