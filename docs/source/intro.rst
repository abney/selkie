
Introduction
============

Selkie is a software library to support **language digitization**,
which is to say, **computational language description** (CLD).
The classic products of language description are a corpus, lexicon,
and grammar, and Selkie supports the production and use of electronic
versions. "Use" includes an implementation of the entire NLP pipeline,
including an automated reasoner at the back end.

Selkie is experimental code, not a finished product - hence version
number 0. Much of it is
under active development and likely to change, sometimes radically, in
the next version. Backwards compatibility cannot be guaranteed.

It is organized as a collection of modules. They vary in the degree to
which they are integrated with one another. To provide a little
structure, I have grouped the modules as follows:

 * **Corpus Editor.**
   The intended users here are linguists and even members of the
   public with interest in language documentation and description.
   The editor and underlying data model integrate texts and
   lexicon, with extensions to grammar intended. In the interests of
   minimizing expertise requirement, the editor runs in a web page.

 * **NLP Pipeline.**
   Viewed at the highest level, a language is a relation between sentences and
   meanings. Accordingly, a central piece of functionality is an
   implementation of that relation, in the form of an NLP
   pipeline that translates natural
   language sentences to a formal semantic representation.
   The pipeline is encapsulated in a conversational agent
   application (selkie.bot), which includes a knowledge base and
   automated reasoner.
   The bot is intended as a testing ground for a grammar as
   digital language description.

 * **Substrate.**
   The substrate packages contain general lower-level functionality.

Installation
------------

Selkie is written in Python, and is installed in the usual way::

    $ pip install selkie

Credits
-------

 * **Census Files.** The files in selkie/data/census were downloaded from
   http://www.census.gov/genealogy/names/,
   though that is now a dead link. (One may instead use
   http://web.archive.org/web/19970617171355/http://www.census.gov/genealogy/names/.)

 * **Danish UD Treebank (Danish Dependency Treebank).** The files in
   selkie/data/conll/UD_Danish-DDT-master were downloaded from
   https://github.com/UniversalDependencies/UD_Danish-DDT/tree/master.
   This is a conversion of the Danish Dependency Treebank to UD format,
   released under the CC-BY-SA-4.0 license
   (https://github.com/UniversalDependencies/UD_Danish-DDT/blob/master/LICENSE.txt),
   which permits redistribution.
   The contributors to the Danish UD Treebank are Anders Johannsen, Hector
   Martinez Alonso, and Barbara Plank. The authors of the original Danish Dependency Treebank are
   Matthias T. Buch-Kromann, Line Mikkelsen, and Stine Kern Lynge.

 * **Gnome Icons.** The following icons in selkie/data/seal are from
   gnome-icon-theme-3.12.0:

   - cog.png
   - gnome/16x16/categories/applications-system.png

 * **ISO Language Codes.** The files in selkie/data/iso were downloaded from:

   - https://www.loc.gov/standards/iso639-2/ascii_8bits.html (ISO 639-2)
   - https://iso639-3.sil.org/ (ISO 639-3)
   - https://www.loc.gov/standards/iso639-5/index.html (ISO 639-5)

 * **LIBSVM.** LIBSVM is written by Chih-Chung Chang and Chih-Jen Lin,
   and is available at http://www.csie.ntu.edu.tw/~cjlin/libsvm. The
   copyright notice (https://www.csie.ntu.edu.tw/~cjlin/libsvm/COPYRIGHT)
   permits redistribution, provided that the copyright notice itself
   is preserved.

 * **Pyfoma.** 

 * **Ply.** The directory ``src/selkie/ply`` contains the PLY lexer
   and parser, written by David Beazley. It is taken from https://github.com/dabeaz/ply.
   According to that page, PLY is a discontinued project, and the
   author recommends copying it into one's own project, which is what
   I have done.

 * **Universal POS Tags.** The files in selkie/data/conll/2006/universal-pos-tags were
   downloaded from https://github.com/slavpetrov/universal-pos-tags.
