
Application and corpus
**********************

Overview
--------

The class CLD (in selkie.cld.core) is the 

an instance of SealApp that
represents the CLD application.  Its contents are represented by the
CLDRequestHandler class, which overrides only two methods of RequestHandler:

 * open_file() - returns a Corpus

 * make_root() - returns a CorpusEditor

The cld_app is used as the application function in a CLDManager.
It can be invoked as::

   $ cld corpus.cld

Manually instantiating the corpus
.................................

The easiest way to get a Corpus instance is to use the CLDManager:

>>> from selkie.cld.toplevel import CLDManager
>>> mgr = CLDManager('/tmp/corpus.cld')
>>> corpus = mgr.corpus()
>>> corpus
<Corpus /tmp/corpus.cld>

Corpus and environment
----------------------

**OUT OF DATE**

.. automodule:: selkie.cld.corpus.core

The Corpus class
................

A Corpus is a
Structure with the following signature.

 * langs (LanguageList) — list of mono-lingual subcorpora

 * users (UserList) — a Collection with child type User

 * roms (Registry) — the central registry of romanizations

 * glab (GLabDirectory)

In addition, a corpus has a _meta member containing a
PropList with general information, and, like all Files,
an env member containing an Environment.

The Environment
...............

The env member is inherited from File, but it gets set by the
Corpus, inasmuch as the Corpus is the root of the disk hierarchy.  See
the section 'Environment' for general
information on environments.  Corpus specializes Database,
which specializes EnvRoot.

When one reaches a Language when descending the hierarchy, a new copy
of the Environment is created that is specific to that language.  The
new copy is used by the Language and its descendants.

An Environment instance has the following members:

 * corpus — A backlink to the Corpus.

 * username — The authorized username, for the purpose of permissions

 * language — Set to the language, if within the scope of a language

 * parent — The original Environment, if this one belongs to a language.

All Environments provide the following methods:

 * for_language(lang) — Create a copy associated with the given language.

 * require_rom(name) — Returns the named
   Romanization.  Signals an error if not found.

 * find_rom(name) — Returns the named
   Romanization, or None if not found.

Language-specific Environments provide the following methods:

 * get_text(id) — Returns the text that has the
   given ID.

 * default_orthography() — Returns the default
   orthography for this language.

 * orthographies() — Returns the list of
   available orthographies for this language.

 * romanization() — Returns the default orthography as a
   Romanization.

 * deref_parid(parid) — Returns the paragraph with the
   given paragraph ID.

Example
.......

An example of opening a corpus and accessing a couple of its members::

   >>> from selkie.cld.corpus import Corpus
   >>> corpus = Corpus('corpus.cld')
   >>> corpus.media.filename()
   '/Users/abney/git/cld/media'
   >>> corpus.langs['oji']
   <selkie.cld.language.Language object at 0x10ac41fd0>

.. automodule:: selkie.cld.ui.corpus

User interface
--------------

Corpus UI
.........

Metadata editor
...............

Catalog of pages
................

The relevant modules all belong to selkie.cld.ui.

 * /home — CorpusEditor (corpus)

 * /langs — LanguageListEditor (language)

 * .../lang.xxx/home — LanguageEditor (language)

 * .../texts/home — TocEditor (toc)


 * .../page/edit — PageEditor (page)

 * .../audio/edit — AudioEditor (audio)

Organization by URL
...................

The most natural starting point for examining code
is often the URL that you use to reach a page.  Each page is generated
by a particular method of an HTML directory instance.  The page
connects to other pieces of source code:
there may be Javascript code associated with the page, placing
callbacks to the HTML directory; and the HTML directory
is generally associated with one or more disk objects.

The quickest way to determine the page and directory associated with a
URL is to run a query in python.
For example, in the directory ~/git/cld, do::

   >>> from selkie.cld.app import App
   >>> app = App('test.cfg')
   >>> app('/langs/lang.oji/texts/text.7/page/xscript/edit.0')
   <HtmlPage Media 33>
   >>> page = _

From the page, one can get the parent (and determine its class)::

   >>> page.__parent__
   <selkie.cld.ui.media.Transcriber object at 0x10bde84a8>

One can also determine the name that was used to access the page::

   >>> page.__file__.name
   'edit.0'

The last directory component of the URL pathname ("xscript",
in our example) often determines a unique directory class.  The
following table lists the associations.

.. list-table::

   * - /
     - CorpusEditor
   * - users
     - GroupsEditor
   * - langs
     - LanguageListEditor
   * - lgsel
     - LanguageSelector
   * - lang.*name*
     - LanguageEditor
   * - texts
     - TocEditor
   * - text.*id*
     - TextEditor
   * - page
     - PageEditor
   * - xscript
     - Transcriber

The following provides an overview of the interface pages.  The names
are classes within selkie.cld.ui, and the arguments are classes
within selkie.cld.

 * CorpusEditor(corpus:Corpus)

    * corpora: CorpusListEditor(contents:CorpusList)

    * lang: LanguageEditor(lang:Language)

    * text: TextEditor

 * langs

    * LanguageListEditor(contents: LanguageList)

    * Search — langs/search

    * Ojibwa — lang.oji

 * lgsel

    * LanguageSelector(langlist: LanguageList)

 * lang.*l*

    * LanguageEditor(lang: Language)

    * Texts — texts

    * Lexicon — lexicon

 * texts, text.*i*

    * TextEditor(text: Text)

    * Redirect — toc, page, stub

 * toc

    * TocEditor(toc: Toc)

 * page

    * PageEditor(page: Page)

    * PlainTextPanel

    * click — igt

 * igt

    * IGTEditor

    * [IGTEditor, LexentViewer]


Corpus file format
------------------

The following table gives the corpus file format.  The root type is
'Corpus.'

All directories contain _children and _perm; they
are not explicitly mentioned in the table.

All files are in tab-separated format.


.. list-table::
   :widths: 3 3 1 6
   :header-rows: 1

 * - Filename
   - Class
   - FD
   - Contents
 * - _children
   - Children
   - F
   - *name suffix*
 * - _config
   - Config
   - F
   - *key value*
 * - _groups
   - GroupsFile
   - F
   - *usr grp*[*(sp)grp**]*
 * - _info
   - PropDict
   - F
   - *key value*
 * - _meta
   - PropDict
   - F
   - *key value*
 * - _perm
   - Permissions
   - F
   - *mode role usr*[*(sp)usr**]
 * - \*.cl
   - ClipsFile
   - F
   - *start end*
 * - \*.cld
   - Corpus
   - D
   - _config _meta _groups
 * - \*.cld
   - Corpus
   - D
   - glab.gd langs.ll roms.reg users.ul
 * - \*.gd
   - GLabDirectory
   - D
   - *user*.gl*
 * - \*.gl
   - Library
   - D
   - *n*.gn*
 * - \*.gn
   - Notebook
   - F
   - (GLab notebook format)</tr>
 * - \*.lg
   - Language
   - D
   - _index _info lexicon.lx texts.toc
 * - \*.ll
   - LanguageList
   - D
   - *lang*.lg*
 * - \*.lx
   - Lexicon
   - F
   - *form sno refs n=value*
 * - \*.mf
   - MediaFile
   - F
   - *usr*/*name*.*suf*
 * - \*.mi
   - MediaIndex
   - F
   - *name*.*suf tid*
 * - \*.pd
   - PropDict
   - F
   - *key value*
 * - \*.pp
   - ParagraphFile
   - F
   - *bool*
 * - \*.reg
   - Registry
   - D
   - *name*.rom
 * - \*.rom
   - Romanization
   - F
   - *ascii unicode*
 * - \*.tf
   - TokenFile
   - F
   - *sentno*
 * - \*.tf
   - TokenFile
   - F
   - nxid *n*
 * - \*.tf
   - TokenFile
   - F
   - *form sno lpunc rpunc*
 * - \*.toc
   - Toc
   - D
   - *id*.txt*
 * - \*.txt
   - Text
   - D
   - _info orig.tf trans.tr?
 * - \*.txt
   - Text
   - D
   - _info media.mf xscript.xs? trans.tr?
 * - \*.txt
   - Text
   - D
   - _info toc.toc
 * - \*.xs
   - Transcription
   - D
   - clips.cl paras.pp transcript.tf
 * - \*.tr
   - Translation
   - F
   - *trans*
 * - \*.ul
   - UserList
   - D
   - *name*.usr*
 * - \*.usr
   - User
   - D
   - media.mi props.pd

CLDManager
----------
