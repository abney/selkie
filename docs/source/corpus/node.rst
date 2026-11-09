
Nodes
=====

General
-------

As discussed in the previous section, the result of reading a corpus
file is a collection of nested dicts (records).
The primary desiderata in the design of the record structure
are simplicity and non-redundancy.

For better support of UI operations, the record and its pieces are accessed via a
higher-level structure consisting of instances of
the class Node. Nodes may be "virtual" elements that package up
information from parts of records or multiple records.

A Node (unlike the record it wraps) contains a backlink to its
parent. This permits us to walk the tree upward and
access contextual information, such as the
``corpus()``, ``language()``, and ``text()`` that a given node
belongs to. Access to the corpus permits any node to ``save()`` all
modifications to the corpus to disk.

Node subclasses
---------------

There are three kinds of node, as follows.

Items
.....

An item is a node that can be selected for viewing or editing
in the UI. It is backed by a record. The Registry item is
an exception, in that its record is not taken directly from
a file. Rather, its key-value pairs represent toplevel
key-value pairs from different corpus files, each file providing a single
pair.

The item structure is a tree that overlies the record tree.
Accordingly, each item is instantiated with a parent node and a
discriminator, and the discriminator is used to
identify the current item's record within the parent item's record.
Modifications to the item translate to modifications to the underlying
record. Items and records stand in one-one correspondence.

When an item is an element in a list, it also has a member
``element_of`` pointing to the list.

There is an Item subclass for each type
of record in the corpus. Subclasses include ``Corpus``,
``Lang``, ``Rom``, ``Text``, ``Lexicon``, ``Trans``, ``Sent``,
``Form``, ``Xlexicon``, ``Xtext``, and ``Times``.

Lists
.....

A list represents a set of records that have the
same type and same parent. For example, a corpus might contain records
with keys ``lang.deu``, ``lang.fla``, ``rom.gothic``, and ``rom.fla``.
(The ISO code 'fla' represents Montana Salish.)
The languages (``lang.deu``, ``lang.fla``) and romanizations (``rom.gothic``,
``rom.fla``) are packaged as two separate lists.
Since all keys in a list have the same attribute, the names uniquely
identify the elements in a list. Note that the names alone do not
uniquely identify a record within the corpus as a whole, however: ``fla`` is the name of
both a language and a romanization.

A List represents a group of children of an item.
The list also includes information about which, if any, child is
currently selected.

The elements of a list must all have the same type. Some items
have more than one type of child, so one should
think of a list as representing *some* of the children of the item,
not necessarily *all* of them.
For example, a
corpus item has two separate lists of children: its languages and its
romanizations.

An element in a list is accessed by discriminator, using square
brackets. 

An item typically provides, for each child list, a member that gives
direct access to the child list. For example,
Corpus has members ``langs`` and ``roms``. One can access the Ojibwe
language in a corpus as ``corpus.langs['oji']``.

Views
.....

A view is associated with a displayable page in the UI. Each item has a
member ``views`` containing a list of views, and each view has a
member ``view_of``, which is an item.

State
-----

A state facilitates user interaction with the corpus. 
One can mark the "current working item" by calling its ``select()`` method.
The state of the corpus then marks the
sequence of **choices** in the pathname leading to that item.

More generally, each Item has a member ``state`` whose value is
a dict that maps child types to Lists. For example, if ``corpus`` is a
corpus, then ``corpus.langs`` is a List of items of type ``lang``;
thus the corpus state maps the key ``"lang"`` to the List ``corpus.langs``.
That is, ``corpus.langs`` and ``corpus.state['lang']`` are two ways to
access the same List.

A List, in turn, has a member ``selected`` whose value is the currently selected
element. For example, if ``reg`` is the registry, then
the currently selected corpus is::

   corpus = reg.state['corp'].selected

Selecting an item causes all of its ancestors that are List elements
to become the selected elements in their Lists.

Descending from a List, one can access additional selections recursively, for example::

   lang = corpus.state['lang'].selected

The states and selected elements define a **selection tree**.

Every Item has a method ``choices()`` that returns an iteration over
the Lists that are encountered in a preorder walk of the selection tree.

The choices support the construction of menus in the user interface,
with one menu per List. Depending on which items are selected,
one might have a menu of corpora, a menu of languages (for the
selected corpus), a menu of texts (for the selected language), etc.
