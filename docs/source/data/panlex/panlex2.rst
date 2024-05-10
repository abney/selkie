
Panlex
******

Panlex2
-------

This is a replacement for the previous version.

Usage
.....

Usage::

   $ python -m seal.script.panlex2 COM ARG*

Some of the commands are actually multi-word commands, in
particular, all the commands beginning with "compile."

 * lang CODE
   — 
   CODE is an ISO 639-3 language code.
   Prints out information about all varieties of the language with the
   given code.  The printout includes the LVID code for each variety
   and the list of dictionaries (SIDs) for each variety.

 * lvid LVID
   — 
   Produces the same output as lang, but limited to a single
   variety.

 * dict SID
   — Prints out metadata for the dictionary whose "source ID" is SID.

 * compile varieties
   — Writes varieties.tab.  Needed for e.g. compile bilex.

 * compile bilex TGT [GLS]
   —
   TGT and GLS must be language variety IDs.
   If GLS is not given it defaults to 187 (English).
   Writes the file bilex-TLVID-GLVID.tab,
   which contains records of form *tgt_str gloss_str sids,*
   where *sids* is a space-separate list of source IDs.

Environment
...........

The following variables must be set in ~/.selkie:

 * data.panlex.zipfn
   — The pathname of the Panlex zip file.  It may begin with "~".

 * data.panlex.dirname
   — The toplevel directory in the zip file, e.g. "panlex-20190901-csv".

 * data.panlex.tgtdir
   — The directory in which to install compiled dictionaries, etc.
   It may begin with "~".



Overview
--------

Panlex is a relational database representing lexical information for
the world's languages.  The information is drawn typically from
bilingual dictionaries.  Accordingly, a dictionary is viewed as consisting of
lexical entries ("meanings"), each of which is the pairing of
an expression in the target language with an expression in the
glossing language, such as::

   boojoo[oji] hello[eng]

Generalizing, multiple target languages and
multiple glossing languages are allowed.  An example is a multilingual
dictionary of several related languages, glossed in both English and
French.  Viewed this way, there is actually little need to distinguish
between target language and glossing language: a lexical entry
is simply a set of synonymous expressions in multiple languages.

Panlex includes some additional lexical information, such as parts
of speech, properties, definitions, and semantic fields.  Definitions and semantic
fields are associated with lexical entries, but parts of speech and
properties are permitted to differ between a word and its gloss.  We should revise
the previous example to::

   boojoo[oji]/int hello[eng]/int

This lexical entry consists of two fields: boojoo[oj]/int
and hello[eng]/int.  A field is intrinsic to a lexical
entry.  Even if an apparently identical field occurs in a different
lexical entry, Panlex treats it as a distinct object.

Hence, the main data types are as follows.

 * An **expression** is a piece of text that is explicitly labeled with
   the language it is written in, like "boojoo[oji]."
   An expression is represented in the
   database by an **expression ID (exid).**
   The ex table associates an exid with a string and language variety.

 * A **field,** which Panlex calls a "denotation," contains
   an expression, has a part of
   speech ("word class"), and may have properties.  A field is represented by
   a **field ID (fid).**  The expression and lexical entry for
   a given fid are specified in the dn table.  The part of
   speech is given in the wc table.  The list of properties
   is given in the table md.

 * A **lexical entry,** which Panlex calls a "meaning," is represented by
   a **lexical-entry ID (lxid).**  I use the term *lexical entry*
   rather than *meaning*, because the object in question is dictionary-specific.
   No attempt is made to identify
   sameness of meaning across dictionaries.
   The association between lxid and dictionary is given in
   the mn table.
   A lxid may also be associated with a definition, in the df
   table, or with a semantic domain, in the dm table.

 * A **dictionary,** which Panlex calls a "source" or "approver,"
   consists of a list of lexical entries, plus metadata.
   A dictionary is represented by a **dictionary ID (did).**
   The association between did and lxids is given in the table mn,
   and dictionary metadata is given in the table ap.

 * A **language variety** may be documented in multiple
   dictionaries, and a dictionary may document multiple language varieties.
   A language variety is represented by a **language variety ID (lvid).**
   The Panlex code for a language variety is of form abc-123,
   consisting of a three-letter **iso code** for the language and a
   three-digit **variety code.**  The association between lvids
   and dids is given in the av table.  The iso code and
   variety code are given in the lv table.

Data tables
-----------

Data types
..........

The data-type specifications used in the data tables are as follows.
The most important are:

 * *exid* - Expression

 * *fid* - Field

 * *lxid* - Lexical entry

 * *did* - Dictionary

 * *lvid* - Language variety

Supporting data types are as follows.

 * *bool* - t or f.

 * *num* - A number.

 * *str* - A string.

 * *char* - A Unicode code point.

 * *date* - A date.

 * *url* - A URL.

 * *iso* - A 3-letter ISO language code.

 * *vc* - A 3-digit Panlex variety code.

 * *lic2* - A 2-letter license code.

 * *fm* - A file format (?)

Expressions
...........

Expressions are used not only for words in dictionaries but also for
parts of speech and dictionary names.
An expression is a word in a particular language variety.  It pairs a
string with a language-variety ID.

``ex``

 * ex (*exid*) — The expression.

 * lv (*lvid*) — Its language variety.

 * tt (*str*) — Its string.

 * td (*str*) — A "degraded text"
   version of the string.  Contains only lowercase
   letters and digits.

Fields
......


A field belongs to a particular lexical entry, and its contents is an
expression.

``dn``

 * dn (*fid*) — The field.

 * mn (*lxid*) — The lexical entry it
   belongs to.

 * ex (*exid*) — The contents.

A part of speech may be assigned to a field.

``wc``

 * wc (*num*) — An ID for the assignment?

 * dn (*fid*) — The field.

 * ex (*exid*) — The part of speech.

The wcex table is a convenience listing of the expressions
that are used as parts of speech.

``wcex``

 * ex (*exid*) — The part-of-speech expression.

 * tt (*str*) — The part-of-speech string.

A field may have properties (key-value pairs).  These are used
for declension classes, valency, etc.

``md``

 * md (*num*) — An ID for the assignment?

 * dn (*fid*) — The field.

 * vb (*str*) — The key.

 * vl (*str*) — The value.

Lexical entries
...............

A dictionary is a list of lexical entries.  Panlex calls them "meanings."

``mn``

 * mn (*lxid*) — The lexical entry.

 * ap (*did*) — The dictionary it belongs to.
   The table is sorted by this column.

The df table appears to represent definitions or explanations.
Not all dictionaries have them.

``df``

 * df (*num*) — The definition ID (?)

 * mn (*lxid*) — The lexical entry.

 * lv (*lvid*) — The language variety of the definition text.

 * tt (*str*) — The definition text.

The dm table appears to represent the semantic domain of an
entry.  Not all dictionaries include it.

``dm``

 * dm (*num*) — The semantic domain (?)

 * mn (*lxid*) — The lexical entry.

 * ex (*exid*) — An expression naming
   the semantic domain

An additional table, mi, also provides information about
lexical entries.  I have not been able to determine what it
represents.  The values in the tt
field are usually IDs of some sort, but occasionally English words.

``mi``

 * mn (*lxid*) — The lexical entry.

 * tt (?) — ?

Dictionaries
............

A dictionary contains a list of lexical entries (see above).
Metadata information is contained in the table ap.

``ap``

 * ap (*did*) — The dictionary ID.

 * dt (*date*) — Registration date.

 * tt (*str*) — A short identifier, e.g. eng-ciw:Weshki.

 * ur (*url*) — The URL.

 * bn (*str*) — ISBN, perhaps?

 * au (*str*) — Author.

 * ti (*str*) — Title.

 * pb (*str*) — Publisher.

 * yr (*str*) — Year of publication.

 * uq (*num*) — Quality?

 * ui (*did*) — Appears to be the same as ap.

 * ul (*str*) — Some kind of summary line.

 * li (*lic2*) — An IP license code.

 * ip (*str*) — An IP license statement.

 * co (*str*) — Company?

 * ad (*str*) — Email address

A dictionary documents one or more language varieties.

``av``

 * ap (*did*) — The dictionary.

 * lv (*lvid*) — A variety that it documents.

The apli table appears to map 2-letter license codes to
3-letter codes.  I don't know what the codes mean.

``apli``

 * id (*num*) — ID for the assignment (?)

 * li (*lic2*) — 2-letter code

 * pl (*?*) — 3-letter code

The table af appears to indicate the file format of the original
source for the dictionary.

``af``

 * ap (*did*) — The dictionary.

 * fm (*fm*) — The format.  Example values are html,
   html-curl, pdf-lock/encrypt, txt, txt-wb,
   xml, pdf-img, and db.

The fm table appears to contain information about "fm" codes.

``fm``

 * fm (*fm*) — Format ID?

 * tt (*str*) — Dictionary name??

 * md (*str*) — ?

The table aped appears to contain Panlex processing information
for dictionaries.

``aped``

 * ap (*did*) — The dictionary.

 * q  (*bool*) — ?

 * cx (*num*) — ?

 * im (*bool*) — ?

 * re (*bool*) — ?

 * ed (?) — ?

 * fp (?) — A code that seems to indicate the documented
   varieties and a one-word abbreviation of the title.  E.g., eng-ciw-Weshki.

 * etc (*str*) — Appears to be comments about what work
   needs to be done yet.

Language varieties
..................

Languages are identified by 3-digit ISO codes.  A language variety is
a specialization.  The varieties of a given language are numbered from
0: eng0, eng1, etc.  There is also a numeric ID for each
language variety.  For example, variety 187 is eng0.
<table class="display">

 * lv (*lvid*) — The language variety.

 * lc (*iso*) — Its ISO language code.

 * vc (*vc*) — Language-variety sequence number.  The varieties of a
   particular ISO-coded language are numbered sequentially from 0.

 * sy (*bool*) — ?

 * am (*bool*) — ?

 * ex (*exid*) — The name of the variety.  Names are usually given in
   the variety (e.g., the name for German is given as "Deutsch."
   But sometimes names are given in English.

Additional information about language varieties is given in tables
cp and cu.  I don't know what these tables contain,
possibly punctuation characters in the language.

``cp``

 * lv (*lvid*) — A language variety.

 * c0 (*char*) — A code point.

 * c1 (*char*) — A code point.

``cu``

 * lv (*lvid*) — A language variety.

 * c0 (*char*) — A code point.

 * c1 (*char*) — A code point.

 * loc (?) — ?

 * vb (?) — Values include pun, priv, aux,
   cit:fin:pri, cit:kom:pri.

Panlex executable
-----------------

Zip
...

One can examine the contents of the original zip file using the
zip command.  There are four subcommands:

 * list — List the filenames.

 * head *f* — Print the first 50 records of file *f*.

 * cat *f* — Print all the records of file *f*.

 * table *f* — The table is like the contents, except that, if
   there is a field labeled ex, two new columns are added: ex.tt
   and ex.lv.  The former contains the string contents of the
   expression and the latter is the language-variety code for the
   expression.  One may optionally provide an attribute *a* and value *v* to
   restrict the listing to records that have value *v* for attribute *a*.
   Nota bene: this command is generally *much* slower than cat.

Variety
.......

A language is a set of varieties::

   $ panlex variety deu
   lv | lc | vc | sy | am | ex | ex.tt | ex.lv
   157 | deu | 0 | t | t | 274 | Deutsch | 157
   1349 | deu | 1 | t | t | 18586881 | Masematte | 1349
   1845 | deu | 2 | t | t | 18586883 | Hessisch | 1845
   9097 | deu | 3 | t | t | 12660638 | doitS | 9097

These are all the language varieties corresponding to ISO code
"deu."  Language variety 157 is deu0, variety 1349 is deu1, and so
on.  I don't know what "sy" and "am" are.  The name of the variety
is given in the variety itself.  Specifically, an expression (ex) is
the pairing of a string (ex.tt) with an indiciation of which variety it is
written in (ex.lv).

To give another example, Ojibwe (oji) is a macrolanguage comprising
Severn Ojibwa (ojs), Eastern Ojibwa (ojg), Central Ojibwa (ojc),
Northwestern Ojibwa (ojb), Western Ojibwa (ojw), Chippewa (ciw),
Ottawa (otw), and Algonquin (alq)::

   $ panlex variety oji ojs ojg ojc ojb ojw ciw otw alq
   lv | lc | vc | sy | am | ex | ex.tt | ex.lv
   30 | ojb | 0 | t | t | 18592962 | Anishinaabemowin | 30
   536 | ciw | 0 | t | t | 18586345 | Anishinaabemowin | 536
   934 | otw | 0 | t | t | 18593131 | Daawaamwin | 934
   4069 | ojw | 0 | t | t | 18592975 | Nakaw?mowin | 4069
   5598 | ojs | 1 | t | t | 7505858 | ????? | 5598
   6930 | ojg | 0 | t | t | 18592966 | Nishnaabemwin | 6930
   6931 | ojc | 0 | t | t | 18592964 | Ojibwe | 6931
   6932 | ojs | 0 | t | t | 18592970 | Anishininiimowin | 6932
   6933 | ciw | 1 | t | t | 8150 | Central Minnesota Chippewa | 187
   7415 | ciw | 2 | t | t | 17070963 | Minnesota Ojibwe | 187
   9170 | alq | 1 | t | t | 241072 | ???????? | 9170
   19 | alq | 0 | t | t | 45808 | anicin?bemowin | 19

The question marks represent Unicode characters that Latex does not handle.
The information here does not appear to be entirely correct.  Panlex
labels a wordlist that Margaret and Howard produced as documenting
variety 536 (ciw0), which is Chippewa.  I would have thought that they
speak Eastern Ojibwa.

Dicts
.....

For each variety, there is a set of
dictionaries::

   $ panlex dicts 30 536 934 4069 5598 6930 6931 6932 6933 7415 9170 19
   128 | Freelang Ojibwe-English dictionary | 13741 | eng-ciw-Weshki
   153 | Freelang Ojibwe-English dictionary | 1319 | ciw-ojw-ojc-ojs-ojg-otw-mic-pot-eng-Weshki
   611 | Astronomia Terminaro | 2474 | mul-Rapley
   2409 | Swadesh Lists | 207 | art-mul-SL
   2815 | Anishinaabemowinâ€“English | 131 | ciw-eng-Noori
   2830 | Ezhi-Giigidaang, How We Say It (Pronunciation) | 0 | ciw-eng-Kimewon
   4091 | Lexique de la langue algonquine | 0 | alq-fra-Cuoq
   3778 | Ojibwe Vocabulary Project | 0 | ciw-eng-Manidoons
   3779 | Ojibwe-English Wordlist | 0 | ciw-eng-Weshki
   4095 | Travels through the Canadas: Vocabulary of the Algonquin Tongue | 0 | alq-eng-Heriot
   4144 | The Ojibwe Peopleâ€™s Dictionary | 0 | eng-ciw-OPD

A dictionary may document more than one variety.

Dict
....

To see information about a dictionary::

   $ panlex dict 128
   ap | lv
   128 | 187
   128 | 536
   
   id 128
   dt 2007-12-11
   tt eng-ciw:Weshki
   ur http://www.freelang.net/dictionary/ojibwe.php
   bn
   au Weshki-ayaad; Charles Lippert; Guy T. Gambill
   ti Freelang Ojibwe-English dictionary
   pb Freelang
   yr 2010
   uq 5
   ui 128
   ul TG 122; FreeLang.English_Ojibwe.wb
   li co
   ip Every author exercises rights with respect to the part of a list that represents that personâ€™s own contribution.
   co Guy T. Gambill
   ad gambillgt1@yahoo.com

The first lines indicate which varieties the dictionary documents.  In
this case, they are 187 (English, eng0) and 536 (Chippewa, ciw0).

Bidicts
.......

To find out which dictionaries document a particular pair of
varieties::

   $ panlex bidicts 187 536
   128 | Freelang Ojibwe-English dictionary | 13741 | eng-ciw-Weshki
   153 | Freelang Ojibwe-English dictionary | 1319 | ciw-ojw-ojc-ojs-ojg-otw-mic-pot-eng-Weshki
   611 | Astronomia Terminaro | 2474 | mul-Rapley
   2409 | Swadesh Lists | 207 | art-mul-SL
   2830 | Ezhi-Giigidaang, How We Say It (Pronunciation) | 0 | ciw-eng-Kimewon
   3778 | Ojibwe Vocabulary Project | 0 | ciw-eng-Manidoons
   4144 | The Ojibwe People's Dictionary | 0 | eng-ciw-OPD

The columns are: dictionary ID (ap.ap) title (ap.ti),
number of entries (count where mn.ap==ap), and short code (aped.fp).

Bidict
......

To extract a bidict::

   $ panlex bidict 128 536 187 | uniq > tmp.out

The result is ASCII sorted (case sensitive), in two-column format,
with a single tab character as column separator.  Let us think of the
first column as the target language and the second column as the
glossing language.  If a target-language word has multiple glosses,
they produce multiple lines in the file, all sharing the same
target-language word.  (Since the file is sorted, they form a
contiguous block.)  For example, the following occurs in the middle of
tmp.out::

   aabizh  cut seams open on
   aabizhiishin    perk up
   aabiziishin     come to
   aabiziishin     revive

For some reason, the dictionaries sometimes contain duplicate
entries - hence the "uniq" in the command line above.

Panlex module
-------------

Zip files
.........

Usage::

   f = open_zipfile()

The Panlex zip file is ~/src/cl/panlex-20140501-csv.zip.

Things you can do with a zip file::

   f.namelist()      # list of filenames
   f.printdir()      # print long listing
   s = f.read(name)  # one of the names from namelist

The entire file is read as a single string.

The list of Panlex files::

   >>> from panlex import open_zipfile
   >>> f = open_zipfile()
   >>> for nm in f.namelist():
   ...     print nm
   ...
   panlex-20140501-csv/
   panlex-20140501-csv/af.csv
   panlex-20140501-csv/mi.csv
   panlex-20140501-csv/aped.csv
   panlex-20140501-csv/df.csv
   panlex-20140501-csv/wc.csv
   panlex-20140501-csv/av.csv
   panlex-20140501-csv/lv.csv
   panlex-20140501-csv/fm.csv
   panlex-20140501-csv/ex.csv
   panlex-20140501-csv/dm.csv
   panlex-20140501-csv/cp.csv
   panlex-20140501-csv/md.csv
   panlex-20140501-csv/dn.csv
   panlex-20140501-csv/cu.csv
   panlex-20140501-csv/ap.csv
   panlex-20140501-csv/wcex.csv
   panlex-20140501-csv/mn.csv
   panlex-20140501-csv/apli.csv

Reading a file
..............

**Raw contents.**::

   s = raw_contents(fn)

The fn omits the directory name and the .csv suffix.  That
is, legitimate values are "af," "mi," etc.

**Reader**.::

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

**Open file**.::

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

**Expand expressions.**::

   r = expand_expressions(recs, hdr)

Returns an iterator over records.  Two new columns are added: the
first contains the expression's string, and the second contains the
expression's variety.

Extracting dictionaries
.......................

**Dict entries.**
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
has the following members and methods.

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
language.  Each denotation generates one line of output, of form::

   m lang v expr degraded pos d e

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
