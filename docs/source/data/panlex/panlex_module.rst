
Panlex module
=============

Example::

   from selkie.panlex import Panlex
   panlex = Panlex(panlex_dir)
   csv = panlex.csv()
   e = csv['langvar']['187']
   csv['expr'][e]

Tables are auto-loaded on demand.  The expr table takes a little more than a minute
to load.

.. py:class:: Panlex

   .. py:method:: __init__(tgtdir)

      This assumes that one has (manually) unzipped the Panlex CSV
      dump file into *tgtdir*.  *Tgtdir* defaults to ``.``.

.. py:class:: Table

   Loads a CSV file.

   .. py:method:: __init__(fn, key=None)

      If *key* is specified, an index is constructed on that key.

   .. py:attribute:: header

      List of strings.

   .. py:attribute:: rows

      A list of lists of strings.

   .. py:method:: __getitem__(k)

      Accesses the index.  Signals an error if there is no index.


Zip files
---------

Example::

   from selkie.panlex import open_zipfile
   f = open_zipfile()

Reading a file
..............

**Raw contents**::

   s = raw_contents(fn)

The fn omits the directory name and the .csv suffix.  That
is, legitimate values are "af," "mi," etc.

**Reader**::

   r = reader(fn)

Uses csv.reader to parse the csv format.
The return value is an iterator over records, each record being a list
of fields.  The first record contains the field names::

   >>> from panlex import reader
   >>> r = reader('af')
   >>> r.next()
   ['ap', 'fm']
   >>> r.next()
   ['1636', '24']

**Open file**::

   (hdr, recs) = open_file(fn)

The header is the list of field names, and recs is an iterator
over the content records.

**Print headers.**
Prints the database schema: the names and headers of all the files::

   >>> from panlex import print_headers
   >>> print_headers()
   af: ap fm
   mi: mn tt
   aped: ap q cx im re ed fp etc
   df: df mn lv tt
   wc: wc dn ex
   av: ap lv
   lv: lv lc vc sy am ex
   fm: fm tt md
   ex: ex lv tt td
   dm: dm mn ex
   cp: lv c0 c1
   md: md dn vb vl
   dn: dn mn ex
   cu: lv c0 c1 loc vb
   ap: ap dt tt ur bn au ti pb yr uq ui ul li ip co ad
   wcex: ex tt
   mn: mn ap
   apli: id li pl

**Head and cat.**
The function head() prints the first *n* records.  The function
cat() dumps the contents readably.  cat(fn,'html')
produces HTML output.

Database tables
...............

**Where**.
Select records containing specified values in a specified field.
The return value is an iterator over records::

   >>> from panlex import where
   >>> for r in where('lv', 'lc', 'deu'):
   ...     print '|'.join(r)
   ...
   157|deu|0|t|t|274
   1349|deu|1|t|t|18586881
   1845|deu|2|t|t|18586883
   9097|deu|3|t|t|12660638

**Expand expressions**::

   r = expand_expressions(recs, hdr)

Returns an iterator over records.  Two new columns are added: the
first contains the expression's string, and the second contains the
expression's variety.

Extracting dictionaries
.......................

**Dict entries**.
The function dict_entry_ids() returns an iterator over the entry IDs
(*lxids*) for a given dictionary or dictionaries::

   >>> from panlex import dict_entries
   >>> len(list(dict_entry_ids('128')))
   13741

The function dict_entry_table() returns a table whose keys are
meaning IDs, and whose values are list of pairs of form (*lvid, w*)
where $w$ is a word string::

   >>> from panlex import dict_entries
   >>> ents = dict_entry_table('128')
   >>> len(ents)
   13741
   >>> mns = list(ents)
   >>> mns[0]
   '2525999'
   >>> ents[mns[0]]
   [('187', 'consider'), ('536', 'naagadawaabam')]
   >>> ents[mns[1]]
   [('187', 'knock against'), ('536', 'bitaakoshkan')]

**Bilex pairs.**
The function bilex_pairs() returns an alphabetically sorted
list of word pairs representing the entries of the given dictionary::

   >>> from panlex import bilex_pairs
   >>> pairs = bilex_pairs('128','536','187')
   >>> pairs[0]
   ['Aabamadong', 'Fort Hope']
   >>> len(pairs)
   13739

Note that the pair of language IDs is not predictable from the
dictionary.  The dictionary may contain more than two languages, and
even if it only contains two, the dictionary does not specify their
order.

The database
------------

Zip file
........

The database dump is contained in a zip file.  The class ZipFile
is used to access it::

   >>> from seal.data.panlex import ZipFile
   >>> zf = ZipFile()

Methods are provided for listing the contents of the zip file::

   >>> zf.ls()
   File Name                                             Modified             Size
   panlex-20140501-csv/                           2014-05-01 03:02:18            0
   panlex-20140501-csv/af.csv                     2014-05-01 03:00:04        38522
   panlex-20140501-csv/mi.csv                     2014-05-01 03:02:00     33214449
   ...
   >>> list(zf.filenames())
   ['af', 'mi', 'aped', 'df', 'wc', 'av', 'lv', 'fm', 'ex', ..., 'apli']

The method print_headers() prints out, for each table, its name and field names.
It takes a minute or two to run::

   >>> zf.print_headers()
   af: ap fm
   mi: mn tt
   aped: ap q cx im re ed fp etc
   ...

To print the contents of the tables, the methods head and cat
are provided::

   >>> zf.head('wcex', 3)
   ex | tt
   3846607 | noun
   3846608 | verb
   >>> zf.cat('wcex')
   ex | tt
   3846607 | noun
   3846608 | verb
   3846609 | adjv
   ...

The method table returns a Table object containing the
contents of the table.  If the table contains an ex field,
two new fields named ex.tt and ex.lv are added to each
record.  This method can be slow to run.

Tables
......

A Table is a collection of records.  It
has the following members and methods::

 * header — A list of strings.

 * records — A list of records, each record being a list of strings.

 * where(*f*,*v*) — Returns a new Table containing the subset
   of records in which field *f* has value *v*.

 * dump() — Prints out the table.

 * grep(*f*,*v*) — Prints out the subtable for which field *f* has
   value *v*.

Parser
......

A Parser instance digests the information in the tables.

Compiler
........

The value of compile is a Compiler instance.  It is used
to create digested files.  If called with no arguments, it creates the
files 

Utility functions
.................

The function attribute_entries() iterates over the records for
a given subject type or a given subject-relation pair.  For example::

   >>> i = attribute_entries('expression', 'label')
   >>> i.next()
   (('expression', 'label', 'string'), '3990756' u'!')

The entries are of form *(t, v_1, v_2),* where *t* is of form
*(t_1, r, t_2)*.

**Collect variety languages.**
The function collect_variety_languages() iterates over the
variety-language records, and constructs a table indexed by variety ID
(an int), whose value is the variety's language.  E.g.::

   >>> vlangs = collect_variety_languages()
   >>> vlangs[187]
   'eng'

**Collect approvers.**
The function collect_approvers() returns a table indexed by
approver ID, in which the values are lists of form [lang, variety,
quality, title].

**Extracting bilexicons.**
A bilexicon is represented in Python by the class Bilex::

   >>> b = Bilex('spa','eng')

**Create raw.**
The first step is to create the raw bilexicon::

   >>> b.create_raw()

This takes about 25 minutes to run.  The output (in this example) is
the file spa-eng-raw.txt in the directory /cl/data/panlex/lex.

The create_raw() method starts by loading the variety-language table, which maps varieties
to their languages.

Then it goes through the expression-variety records, creating a table
of expressions.  The keys are expressions (ints) and the values are
lists of form [variety, label, degraded text].  An entry is created
only for expressions whose variety's language is one of the two
languages of interest.  Label and degraded
text are initially set to the empty string.

Next it goes through the expression-label and expression-degraded-text
records, filling in the other fields of the expression entries.

Next it creates a denotations table.  It
goes through the denotation-expression records.  If the expression has
an entry in the expressions table, then a new entry is created in the
denotations table.  The key is the denotation (an int), and the value
is a list of form [expression, part of speech, meaning].  Initially
only the expression is set.  Part of speech is initialized to the
empty string and meaning is initialized to 0.

Next it goes through the denotation-pos records and the
denotation-meaning records, filling in the remaining fields in the
denotation entries.

By that point, memory is pretty much full.  Output is written to
*lang1-*lang2*-raw.txt*.
We pass through the denotations table.  Each denotation entry contains
an expression ID, we use it to fetch the expression entry.  The
expression entry contains a variety ID; we use it to look up the
language.  Each denotation generates one line of output, of form:
<blockquote>
m lang v expr degraded pos d e
</blockquote>

The single letters represent integer IDs: meaning (m), variety (v),
denotation (d), expression (e).  The denotation and expression IDs are
included only for debugging purposes.

**Sort raw.**
The method sort_raw() calls Unix sort to sort the raw
file by meaning, language, variety, and label.  The output is written
to *lang1-*lang2*-m1.txt*.  It takes a couple minutes
to run.

**Create m2.**
The method create_m2() adds approvers, and also filters out
monolingual meanings.  (I tried adding approvers when creating the raw
file, but Python runs out of memory)::

   >>> b.create_m2()

The method scans through the m1.txt file, collecting a table of
meanings.  For each block of meanings, note is kept of whether both
languages are seen.  If so, an entry is created in the meanings table,
and otherwise no entry is created.  The meanings table is indexed by
meaning ID, and the value is the approver ID (initialized to 0).

After creating the meanings table, the method passes through the
meaning-approver records and sets the values (approvers) for the
meanings.

Next it calls collect_approvers() to get the quality
information for each approver.

Finally, it passes a second time through the m1.txt file.  Each
time it encounters a new meaning, it looks in the meanings table to
see whether it should be kept or not.  If the meaning is a keeper, the
quality of the approver is looked up in the approvers table.  Each
line from m1.txt that is to be kept is copied to m2.txt,
and two new fields are added at the end: approver ID and quality.
Hence the lines in m2.txt are of form::

   m lang v expr degraded pos d e a q

where "a" is approver and "q" is quality (both are ints).

**Create sources.**
The method create_sources() extracts detailed information about
each of the approvers.  It writes the file *lang1*-*lang2*-sources.txt.
The line format is::

   a rel value

where "a" is the approver ID.  The relations (attributes) are:
lang, variety, regdate, label, creator,
isbn, lic_id, license, year, publ,
title, and url.  An empty line is inserted before each
block of records sharing a common value for "a."

**By word.**
The method by_word() creates a file containing lines of form::

   word-lang1 quality word-lang2

The method sort_by_word() then sorts that file.

It turns out that the quality scores for the approvers are not very
informative about whether the entries are actually good.  For example,
the top quality source (quality 7) for the Spanish word "a" includes
meanings "crazy," "missionary," and "physical" - completely
bogus.  A much better gauge appears to be the number of sources in
which the translation occurs.
