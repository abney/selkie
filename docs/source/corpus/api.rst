
Python API — ``selkie.corpus``
==============================

.. py:module:: selkie.corpus

Example
-------

There is a sample corpus in ``selkie.data``::

    >>> from selkie.data import ex
    >>> corpfn = ex('corp28.cld')

Open the corpus by instantiating the Corpus class::

    >>> from selkie.corpus import Corpus
    >>> corpus = Corpus(corpfn)

The methods ``__str__()``, ``save()``, ``export_cld()``, and
``export_json()`` dispatch to the underlying file, which is ``corpus.file``::

    >>> corpus.file
    <File corp28.cld>
    >>> s = str(corpus)
    >>> s = corpus.export_json()

The corpus contains a list of languages::

    >>> langs = corpus.langs
    >>> len(langs)
    1
    >>> list(langs)
    [<Language deu>]
    >>> deu = langs[0]
    >>> deu
    <Language deu>

One can also access languages by ID::

    >>> deu2 = corpus.language('deu')
    >>> deu2 is deu
    True

Going down the hierarchy, a language contains a list of texts::

    >>> len(deu.texts)
    3
    >>> list(deu.texts)
    [<Text deu.1>, <Text deu.2>, <Text deu.3>]
    >>> text2 = deu.texts[1]
    >>> text2
    <Text deu.2>

In addition to texts, a Language also has properties. The ``props``
member behaves like a dict::

    >>> sorted(deu.props)
    ['glot', 'iso3', 'name', 'rom']
    >>> deu.props['glot']
    'stan1295'

The children of a Node all have the same type. A Node may have
additional dependents of other types. Each of them is accessed by a
dedicated method. For example, in addition to its children, which are
texts, a language also contains a lexicon::

    >>> deu.lexicon()
    <Lexicon deu>

Classes
-------

.. py:class:: File

   .. py:attribute:: cob

      A python dict representing the contents of the file.

   .. py:method:: filename()

      A Path or None.

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

.. py:class:: Signature

   .. py:method:: level(ty)

      Returns the level of the given type.

   .. py:method:: children(ty)

      Returns the list of child types for the given
      type, or None if the type is an attribute type.

   .. py:method:: parent(ty)

      Returns the parent type of the given type.

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

