
Overview
********

Selkie is a software library to support **language digitization**,
which is to say, **computational language description** (CLD).
The classic products of language description are a corpus, lexicon,
and grammar, and Selkie supports the production and use of electronic
versions. "Use" includes an implementation of the entire NLP pipeline,
including an automated reasoner at the back end.

Selkie is experimental code, not a finished product. Much of it is
under active development and is likely to change in the
future. Similarly, this documentation is still in draft form.
I am making it publicly available to give easier access to
students and anyone else who may be interested.

Installation
============

Selkie is written in Python, and is installed in the usual way::

    $ pip install selkie

The toplevel modules of Selkie
==============================

**Corpus Editor.**
A central piece of Selkie is an application for creating, editing, and
viewing linguistic corpora. The currently working version is called
CLD ("Computational Language Documentation").

**Next Editor.** The corpus editor is being redesigned. The new
version is still fragmentary.

**The NLP pipeline.**
Viewed at the highest level, a language is a relation between sentences and
meanings. Accordingly, a central piece of functionality is an
implementation of that relation, in the form of an NLP
pipeline that translates natural
language sentences to a formal semantic representation. The pipeline
is currently unidirectional, but the inverse, generating natural
language from a representation of the meaning, is under
development. The pipeline is encapsulated in a conversational agent
application (selkie.bot), which includes a knowledge base and
automated reasoner as a stand-in for the rest of cognition.
The bot is intended as a testing ground for a grammar as
digital language description.

**Dataset interfaces.**
Convenience interfaces to a variety of third-party datasets
are provided, to make it easier to access them and use them for
language description.

**Supporting Packages.**
The supporting packages contain lowlevel functionality that is used across the
components of Selkie.

Credits
=======

 * **Pyfoma.** 

 * **Ply.** The directory ``src/selkie/ply`` contains the PLY lexer
   and parser, written by David Beazley. It is taken from https://github.com/dabeaz/ply.
   According to that page, PLY is a discontinued project, and the
   author recommends copying it into one's own project, which is what
   I have done.

 * **LIBSVM.** LIBSVM is written by Chih-Chung Chang and Chih-Jen Lin,
   and is available at http://www.csie.ntu.edu.tw/~cjlin/libsvm. The
   copyright notice (https://www.csie.ntu.edu.tw/~cjlin/libsvm/COPYRIGHT)
   permits redistribution, provided that the copyright notice itself
   is preserved.

 * **Gnome Icons.** The following icons in selkie/data/seal are from
   gnome-icon-theme-3.12.0:

    - cog.png
    - gnome/16x16/categories/applications-system.png

 * **Census Files.** The files in selkie/data/census were downloaded from
   http://www.census.gov/genealogy/names/,
   though that is now a dead link. (One may instead use
   http://web.archive.org/web/19970617171355/http://www.census.gov/genealogy/names/.)

 * **ISO Language Codes.** The files in selkie/data/iso were downloaded from:

   - https://www.loc.gov/standards/iso639-2/ascii_8bits.html (ISO 639-2)
   - https://iso639-3.sil.org/ (ISO 639-3)
   - https://www.loc.gov/standards/iso639-5/index.html (ISO 639-5)

 * **Universal POS Tags.** The files in selkie/data/conll/2006/universal-pos-tags were
   downloaded from https://github.com/slavpetrov/universal-pos-tags.
