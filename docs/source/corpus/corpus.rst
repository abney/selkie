
Python API — ``selkie.corpus``
==============================

.. py:module:: selkie.corpus

File
----

The contents of a corpus is a hierarchically organized set of
python dicts representing corpus objects (cobs), as described above
("CLD Format").
The toplevel cob is wrapped in an instance of the class ``File``,
which supports the following methods:

.. py:class:: File

   .. py:method:: load(fn)

      Loads the contents from a file, given the
      filename. One may optionally specify create=True to cause the file
      to be created if it does not already exist.

   .. py:method:: read(f)

      Reads the contents from an open stream.

   .. py:method:: parse(s)

      Creates the contents from the string contents of the
      file.

   .. py:method:: save()

      Saves the contents to the file associated with this File
      object. One may optionally provide a filename to do "save as".

   .. py:method:: write(f)

      Writes the contents to an open stream.

   .. py:method:: __str__()

      Produces the string contents of the file.

   .. py:method:: export_cld()

      Produces the string contents in CLD format.

   .. py:method:: export_json()

      Produces the string contents in JSON format.

The file structure is represented by a ``Signature`` object, which
behaves like a regular python dict, and is created by passing in a
regular python dict. The standard signature is::

    {'corpus': {'lang', 'rom'},
     'lang': {'name', 'glot', 'iso3', 'userom', 'text', 'lexicon', 'trans'},
     'rom': {'u'},
     'text': {'ty', 'ti', 'de', 'au', 'ch', 'pdf', 'audio', 'video', 'sent'}
     'lexicon': {'form'},
     'trans': {'xlexicon', 'xtext'},
     'sent': {'w', 'tr', 'times'},
     'form': {'fy', 'g', 'c', 'pp', 'cf', 'of'},
     'xlexicon': {'fg'},
     'xtext': {'sg'},
     'times': {'t'}}

The Signature also provides the following methods:

.. py:class:: Signature

   .. py:method:: level(ty)

      Returns the level of the given type.

   .. py:method:: children(ty)

      Returns the list of child types for the given
      type, or None if the type is an attribute type.

   .. py:method:: parent(ty)

      Returns the parent type of the given type.

Formats
-------

Currently, two file formats are supported: CLD format and JSON
format. A file format is represented by a ``Format`` object, which
provides two methods. The method ``decode()`` takes a string and
converts it to a python dict representing the corpus contents, and the
method ``encode()`` does the reverse computation. (For the JSON
format, these are just ``json.loads()`` and ``json.dumps()``.)

Node
----

A ``Node`` is a wrapper for a cob. It associates a Location and a File
with the cob: the Location makes it easy to go to related cobs, 
and the File makes it easy to save out modifications.

In addition, it treats the cob explicitly as a node in the hierarchical structure of
the corpus. In particular, it behaves like a list of children, children corresponding
to some but not all of the items in the cob. For example, a ``Lang``
behaves like a list of ``Texts``.

Conversely, the node records its
parent and its key relative to the parent. For example, if ``oji`` is
a Lang, its first child has key ``text.1``. It also records its
location in the corpus in the form of a ``Location`` object.

Nodes are lightweight wrappers only. It may easily be the case that
multiple Node instances wrap the same cob. Children and other links
are computed on the fly, so that modifications to a cob
automatically have immediate effect on all Nodes that wrap it.

There is a Node subclass for each variety
of object in the corpus. The subclasses include ``Corpus``, ``Language``, 
``Text``, ``Sentence``, ``Times``, ``Lexicon``, and ``Word``.

.. py:class:: Node

   .. py:attribute:: cob

      The cob that this node wraps.

   .. py:attribute:: parent

      The parent of this node (a Node).

   .. py:attribute:: key

      The key by which one accesses this node in parent.cob.

   .. py:attribute:: file

      The corpus File.

   .. py:attribute:: table

      A Table object. It that behaves like a python dict that provides
      access to the children of this node by key. For example:
      ``node.table['text.1']``. The value is a Node (not just a cob).

   .. py:attribute:: props

      A Props object. It behaves like a python dict that provides
      access to the values of attributes. The values are strings (as
      in the cob), but iterating over it only yields attribute names,
      not all the keys of the cob. Other methods like __len__() and
      items() yield values that differ from those of the cob.

   .. py:method:: __getitem__(i)

      Returns the i-th child (a Node).

   .. py:method:: __iter__()

      Iterates over the children.

   .. py:method:: children()

      A synonym for __iter__().

   .. py:attribute:: location()

      The node's location in the corpus (a Location instance).

   .. py:method:: ancestors()

      Iterates over all the ancestors (following parent links
      recursively).

   .. py:method:: key_type()

      Same as ``split_at_period(node.key)[0]``.

   .. py:method:: full_name()

      A string that unambiguously identifies this node in the
      corpus. E.g., ``lang.oji text.1``.

.. py:class:: Location

   .. py:attribute:: item

      The Node whose location is represented.

   .. py:attribute:: corpus

      The corpus (a Node).

   .. py:attribute:: language

      The Language that this node belongs to, or None.

   .. py:attribute:: text

      The Text that this node belongs to, or None.

   .. py:attribute:: sentence

      The Sent that this node belongs to, or None.

   .. py:attribute:: token

      The Token that this node belongs to, or None.

   .. py:attribute:: word

      The Word associated with this node, or None.

   .. py:attribute:: view

      Locations are used by the UI (selkie.wap) like URLs, to identify
      complete web pages. The UI sets the 'view' attribute to
      distinguish two locations that display differently, but involve
      all the same Nodes.

Example
-------

There is a sample corpus in ``selkie.data``::

    >>> from selkie.data import ex
    >>> corpfn = ex('corp27.cld')

Open the corpus by instantiating the Corpus class::

    >>> from selkie.corpus import Corpus
    >>> corpus = Corpus(corpfn)

The methods ``__str__()``, ``save()``, ``export_cld()``, and
``export_json()`` dispatch to the underlying file, which is ``corpus.file``::

    >>> corpus.file
    <File corp27.cld>
    >>> s = str(corpus)
    >>> print(s[:22])
    lang.deu
      name German
    >>> s = corpus.export_json()
    >>> s[:30]
    '{"lang.deu": {"name": "German"'

The corpus behaves like a list of languages::

    >>> len(corpus)
    1
    >>> list(corpus)
    [<Lang lang.deu>]
    >>> deu = corpus[0]
    >>> deu
    <Lang lang.deu>

The ``table`` member provides access to children by name. It behaves
like a dict::

    >>> deu2 = corpus.table['lang.deu']
    >>> deu2 == deu
    True

Note that Nodes are lightweight wrappers. Each access may create a new
wrapper::

    >>> deu2 is deu
    False

Going down the hierarchy, a language behaves like a list of texts::

    >>> len(deu)
    3
    >>> list(deu)
    [<Text text.1>, <Text text.2>, <Text text.3>]
    >>> text = deu[1]
    >>> text
    <Text text.2>

In addition to children, a Node also has properties. The ``props``
member behaves like a dict::

    >>> sorted(deu.props)
    ['glot', 'iso3', 'name', 'userom']
    >>> deu.props['glot']
    'stan1295'

The children of a Node all have the same type. A Node may have
additional dependents of other types. Each of them is accessed by a
dedicated method. For example, in addition to its children, which are
texts, a language also contains a lexicon::

    >>> deu.lexicon()
    <Lexicon lexicon>

