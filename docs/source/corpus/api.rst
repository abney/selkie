
Python API — ``selkie.corpus``
==============================

.. py:module:: selkie.corpus

Example
-------

There is a sample corpus in ``selkie.data``::

   >>> from selkie.data import ex
   >>> corpfn = ex('corp29.cld')

Open the corpus using ``open_corpus()``::

   >>> from selkie.corpus import open_corpus
   >>> corpus = open_corpus(corpfn)
   >>> corpus
   <Corpus corp29>

The function ``open_corpus()`` creates an empty Registry as parent of
the corpus::
  
   >>> corpus.parent
   <Registry>

The method ``__str__()`` dispatches to the underlying file (``corpus.file``)::

   >>> print(str(corpus)[:42])
   #!selkie file cld29
   corp.corp29
     lang.deu

Similarly for ``save()``, ``export_cld()``, and ``export_json()``. For example::

   >>> print(corpus.export_cld()[:40])
   #!selkie file cld29
   corp.corp29
   lang.deu
   >>> print(corpus.export_json()[:30])
   {"corp.corp29": {"lang.deu": {

The underlying record::

   >>> type(corpus.record)
   <class 'dict'>
   >>> list(corpus.record)
   ['lang.deu']

The corpus contains a list of languages::

   >>> corpus.langs
   <List of Language>
   >>> len(corpus.langs)
   1
   >>> deu = corpus.langs[0]
   >>> deu
   <Language deu>

Lists accept both numeric indices, as just shown, or discriminators::

   >>> corpus.langs['deu']
   <Language deu>

Each item has an item ID::

   >>> deu.itemid
   'deu'

Each item also has properties. The ``props`` member behaves like a dict::

    >>> sorted(deu.props)
    ['glot', 'iso3', 'name', 'rom']
    >>> deu.props['glot']
    'stan1295'

Going down the hierarchy, a language contains a list of texts::

   >>> texts = deu.texts
   >>> len(texts)
   3
   >>> list(texts)
   [<Text deu.1>, <Text deu.2>, <Text deu.3>]
   >>> text2 = texts[1]
   >>> text2
   <Text deu.2>

The children of a node all have the same type. A node may have
additional dependents of other types. Each of them is accessed by a
dedicated method. For example, in addition to its children, which are
texts, a language also contains a lexicon::

   >>> deu.lexicon()
   <Lexicon deu>

Items also have views, which serve as the leaves of the hierarchy::

   >>> deu.views
   [<Props deu>, <Toc deu>]
   
One can walk back up the hierarchy for contextual information,
including ``language()``, ``corpus()``, and ``root()``::

   >>> text2.language()
   <Language deu>
   >>> text2.corpus()
   <Corpus corp29>
   >>> text2.root()
   <Registry>

Finally, items have state information. Global state information is the
state of the root::
  
   >>> registry = text2.root()
   >>> registry.state
   {'corp': <List of Corpus>}

The method ``choices()`` can be called from any node. It starts with
the root state and walks downward through the lists that it
encounters, going from a list to the state of its selected item, if
any. Initially, nothing is selected::

   >>> registry.corpora.selected is None
   True
   >>> corpus.langs.selected is None
   True
   >>> deu.texts.selected is None
   True
   >>> for lst in text2.choices(): print(lst, repr(lst.selected))
   <List of Corpus> None

One can select either an item or a view. If one selects a
view, it becomes the ``current_view`` of its parent and causes its
parent (item) to be selected. If one selects an item, its first available
view becomes the current view, if it does not already have a current
view. Then the item and each of its ancestors is made the selected
element in its list, if it is an element of a list::

   >>> text2.select()
   >>> text2.current_view
   <Props deu.2>
   >>> for lst in text2.choices(): print(lst, repr(lst.selected))
   <List of Corpus> <Corpus corp29>
   <List of Language> <Language deu>
   <List of Text> <Text deu.2>
   <List of Sentence> None
   <List of Rom> None

For debugging purposes, the method ``print_state()`` is also
provided. Like ``choices()``, it can be called from any node::

   >>> text2.print_state()
   corp:
     <Corpus corp29> == selected
       lang:
         <Language deu> == selected
           text:
             <Text deu.1> 
             <Text deu.2> == selected
               sent:
                 <Sentence deu.2.1> 
                 <Sentence deu.2.2> 
             <Text deu.3> 
       rom:


Functions
---------

.. py:function:: open_cld_file(fn)

   Opens a file in CLD format and returns a File object.

.. py:function:: open_corpus(fn)

   Opens a file in CLD format and returns a Corpus object. An empty
   Registry is created to be the parent.

Generic classes
---------------

.. py:class:: Node

   .. py:attribute:: parent

      The parent of this node (a Node).

   .. py:method:: root()

      Returns the root node (a Registry).

   .. py:method:: corpus()

      Returns the Corpus that this node belongs to.

   .. py:method:: language()

      Returns the Language that this node belongs to.

   .. py:method:: text()

      Returns the Text that this node belongs to.

   .. py:method:: sentence()

      Returns the Sentence that this node belongs to.

   .. py:method:: choices()

      Walks the root state recursively, going from state to list to
      selected element's state. Iterates over the lists.

   .. py:method:: print_state()

      Prints out the choices in a readable format.

.. py:class:: Item

   A specialization of Node.

   .. py:attribute:: TypeString
		     
      Set for each specialization of Item. The record type name
      corresponding to this class of Item.

   .. py:attribute:: name

      The discriminator, or None.

   .. py:attribute:: element_of

      The list that this element belongs to, or None.

   .. py:attribute:: views

      A List of Views.

   .. py:attribute:: current_view

      An element of views, or None.

   .. py:attribute:: state

      A dict with items (*key*, *value*), where
      *value* is a child-list of this item, and the corresponding *key*
      is the TypeString of the list's ElementClass.

   .. py:attribute:: itemid

      A string; dot-separated discriminators from the corpus down to
      this node.

   .. py:attribute:: record

      The underlying record.

   .. py:method:: display_string()

      Returns the TypeString plus the itemid (a string).

   .. py:method:: add_children(lst)

      Records the *lst* in this item's state.

   .. py:method:: add_views(*views)

      Adds *views* to this item's list of views.

   .. py:method:: select()

      Select this item. If it does not already have a value for
      ``current_view``, it is set to the first view on
      the list ``views``. This item, and each of its ancestors,
      becomes the selected element of its list, if it belongs to a
      list.

.. py:class:: List
   
   List is a specialization of Node.

   .. py:attribute:: ElementClass

      The class of elements of this list.

   .. py:attribute:: elements

      The elements.

   .. py:attribute:: selected

      A member of elements, or None.

   .. py:method:: __len__()

      Returns the number of elements.

   .. py:method:: __getitem__(name)

      Returns the element with the given name, if name is a string, or
      at the given position, if name is an int.

   .. py:method:: get(name)

      Like ``__getitem__()``, but returns None if the element does not
      exist. It does not accept a numeric argument.

   .. py:method:: __iter__()

      Returns an iteration over the elements.

.. py:class:: View

   A specialization of Node.

   .. py:attribute:: Page

      The UI page.

   .. py:attribute:: view_of

      The item that this is a view of.

   .. py:method:: select()

      Make this view be the ``current_view`` of its parent, and select
      the parent.

.. py:class:: Props

   A specialization of View that represents a dict of properties.
   It implements the usual dict methods.   

Corpus items
------------

.. py:class:: Registry

   A specialization of Item.

   .. py:attribute:: corpora

      A Corpora object, which is a list.

   .. py:method:: __iter__()

      Iterates over the Corpora.

   .. py:method:: __len__()

      Returns the number of corpora.

   .. py:method:: __getitem__(name)

      Returns the corpus with the given name (discriminator),
      or at the given position, if *name* is an integer.

   .. py:method:: get(name)

      Like ``__getitem__()``, but returns None if the name is not present.

   .. py:method:: open(fn)

      Opens and returns a corpus. If the named file does not exist, an
      empty corpus is returned.

   .. py:method:: new()

      Creates and returns a new corpus, with a name beginning with ``untitled-``.

.. py:class:: Corpus

   .. py:attribute:: file

      The file.

   .. py:attribute:: props

      Properties of the corpus.

   .. py:attribute:: langs

      List of langs (type: Langs).

   .. py:attribute:: roms

      List of roms (type: Roms).

   .. py:method:: export_cld()

      Returns the contents in CLD format (a string).

   .. py:method:: export_json()

      Returns the contents in JSON format (a string).

   .. py:method:: save()

      Save the file.

   .. py:method:: rename(name)

      Rename the file. It also updates the corpus properties.

   .. py:method:: __str__()

      Identical to ``export_cld()``.

.. py:class:: Language

   .. py:attribute:: props

      Its properties.

   .. py:attribute:: texts

      An instance of Texts.

   .. py:attribute:: toc

      The Toc (table of contents). A hierarchical representation of
      the texts.

   .. py:attribute:: lexicon

      The Lexicon.

.. py:class:: Rom

   A romanization.

.. py:class:: Text

   .. py:attribute:: props

      The properties of the text.

   .. py:attribute:: sents

      The Sents.

   .. py:method:: title()

      Returns the text's title, or ``(untitled)`` if it has none.

   .. py:method:: children()

      Returns the text's children, as Text objects. It uses the ``ch``
      feature, and looks up the names in the language's ``texts``.
      It silently suppresses any name that is not found in ``texts``.

.. py:class:: Lexicon

   A lexicon.

.. py:class:: Trans

   A secondary glossing.

.. py:class:: Sentence

   .. py:attribute:: tokens

      The Tokens of the sentence.

   .. py:method:: string()

      The string of the sentence.

   .. py:method:: set_string(s)

      Replaces the contents of the sentence. Causes ``tokens`` to be rebuilt.

   .. py:method:: __len__()

      Returns the number of tokens.

   .. py:method:: __iter__()

      Iterates over the tokens.

   .. py:method:: __getitem__(i)

      Returns a token by position.

.. py:class:: Tokens

   A View representing the tokens of a sentence. Implements the usual
   list methods.

.. py:class:: Form

   An entry in a lexicon.

.. py:class:: Xlexicon

   A collection of secondary word glosses.

.. py:class:: Xtext

   A collection of secondary sentence glosses.

.. py:class:: Times

   The time points of a transcribed sentence.

.. py:class:: Token

   .. py:attribute:: idx

      The position in the sentence.

   .. py:attribute:: string

      The token string.

.. py:class:: Toc

   Table of contents.

Lists
-----

.. py:class:: Corpora

   A specialization of List whose elements are of class Corpus.

.. py:class:: Langs

   A specialization of List whose elements are instances of Language.

.. py:class:: Roms

   A specialization of List whose elements are instances of Rom.

.. py:class:: Texts

   A specialization of List whose elements are instances of Text.

.. py:class:: Sents

   A specialization of List whose elements are instances of Sentence.
