
Languages
*********

.. automodule:: selkie.cld.corpus.language

Language list
-------------

LanguageList
............

The contents of corpus.langs is a LanguageList,
which is a Collection of Language instances
named by ISO 639-3 language codes::

    >>> langs = corpus.langs
    >>> sorted(langs)
    ['eng', 'otw']
    >>> eng = langs['eng']
    >>> eng
    <Language langs/eng>

One creates a new language using the Collection method
new_child()::

   >>> otw = langs.new_child('otw')

The change is immediately saved to disk.  If we reload the corpus, it
is present::

   >>> corpus = load_corpus('/tmp/corpus.cld')
   >>> langs = corpus.langs
   >>> sorted(langs)
   ['eng', 'otw']
   >>> eng = langs['eng']
   >>> otw = langs['otw']

.. automodule:: selkie.cld.ui.language

LanguageListEditor
..................

The object at /langs is a LanguageListEditor.
Its contents is a LanguageList.
It provides the following pages:

 * /, view — Displays the list of languages.  Each link directs to
   ./lang.*code*/.  If the user has write permission,
   there is also a "$+$" link, which directs to ./add/,
   and a "Search" button, which links to ./lgsel/.  

 * lang.*code* — If the *code* is in the
   LanguageList, return a LanguageEditor editing the
   language contents[*code]*.  Otherwise, return a
   page to confirm that one wishes to add the language.
   The confirmation page prints out information about the language, so
   that one can verify which language it is, and provides two buttons:
   the "Confirm" button links to confirmed.*code* and the
   "Cancel" button takes one back to view.

 * confirmed.*code* — If the *code* is valid,
   create a new language and redirect to ./lang.*code.*
   Otherwise return a "Not a Language" page with a "Return" link
   to ./.

 * add, lgsel — Takes one to a LanguageSelector.

LanguageSelector
................

The object at /langs/add or /langs/lgsel is a
LanguageSelector, with member langlist of type
LanguageList.  It provides the following pages:

 * /, view — A page providing two search boxes: one by language
   code and one by name or name part.  The language code box posts to
   bycode, and the name box posts to search_results.

 * bycode — If the submit reason is "Cancel," redirects to ../.
   Otherwise, returns the same page as selected.*code*.

 * selected.*code* — Displays the database information about
   the language with the given *code* and provides two buttons: "Confirm"
   and "Cancel."  "Confirm" links to commit.*code,* and "Cancel"
   links to ./.  However, if the *code* is invalid, it
   returns a "Not a Language" error page with a "Back" link to ./.

 * commit.*code —* If the *code* is valid, redirects to
   ../confirmed.*code*.  Otherwise returns the "Not a
   Language" page.

Language
--------

A Language is a Structure with the following
signature:

 * texts (Toc) — a Toc instance.

 * info (Dict) — general properties.</td></tr>

 * lexicon (Lexicon) — the lexicon for this language.</td></tr>

 * course (Course)

The info member contains general information
about the language.  It is initially empty.
The only keys that are currently used are
'orthographies' and 'default_orthography'.
The value for the former is a comma-separated list of romanization names,
and the value of the latter is a single romanization name.

Language provides methods orthographies() and
default_orthography().  They consult the info dict, but
supply a default if the dict is empty.  The default orthography is
called 'default'::

   >>> list(eng.info)
   []
   >>> eng.default_orthography()
   'default'
   >>> eng.orthographies()
   ['default']

 * dbentry() —
   Returns the
   entry from the language database in seal.data.langdb.
   The database is loaded from the following files:

    * data/iso/639-3: main file, name index,
      macrolanguages, retirements.

    * data/iso/639-5.txt: language groups.

    * data/seal/*.rom: romanizations.

Editor
------
