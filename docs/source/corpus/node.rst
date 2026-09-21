
Nodes
=====

General
-------

The result of reading a corpus file is a single large python dict (a
cob), containing a single key, with prefix ``corp``.
The primary desiderata in the design of the cob structure
are simplicity and non-redundancy.

For better support of UI operations, the cob and its pieces are accessed via a
higher-level structure consisting of instances of
the class Node. Nodes may be "virtual" elements that do not stand
in one-one correspondence with the cobs.

There are three kinds of node:

 * An **item** is a node that can be selected for viewing or editing
   in the UI. It is backed by a cob. (The Registry item is
   exceptional, in the sense that its cobe is not taken directly from
   a file. Rather, its key-value pairs represent toplevel
   key-value pairs from corpus files, each file providing a single
   pair.)

 * A **view** pairs an item with a UI Page. Each item has a
   member ``views`` containing a list of views, and each view has a
   member ``view_of``, which is an item.

 * A **list** is a node that represents a set of sub-cobs that have a
   common object type. A list, like an item, is taken from a corpus
   file, but it has no cob of it own. Its elements correspond to a
   subset of key-value pairs from its parent's cob.

Nodes also record **state** information for the UI. In particular, at any point in
time, the user may have selected a particular corpus, a particular
language within the corpus, a particular text within the language, and
so on, and that information is represented in the node
structure.

All Nodes are instantiated with a parent. Walking the tree upward
gives access to contextual information, including the
``corpus()``, ``language()``, and ``text()`` that a given node
belongs to. Access to the corpus permits any node to ``save()`` all
modifications to the corpus to disk. Moreover, the corpus contains an
index that allows one to access arbitrary items (within the same
corpus) by type and itemid.

Items
-----

The item structure is a tree that overlies the cob tree.
Accordingly, each item is instantiated with a parent node and a
discriminator, and the discriminator is used to
identify the current item's cob relative to the parent item's cob.
Modifications to the item translate to modifications to the underlying
cob. Items and cobs stand in one-one correspondence.

When an item is an element in a list, it also has a member
``element_of`` pointing to the list.

There is an Item subclass for each type
of object in the corpus. Subclasses include ``Corpus``,
``Lang``, ``Rom``, ``Text``, ``Lexicon``, ``Trans``, ``Sent``,
``Form``, ``Xlexicon``, ``Xtext``, and ``Times``.

Lists
-----

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

Each item provides members that contain the child lists. For example,
Corpus has members ``langs`` and ``roms``. One can access the Ojibwe
language in a corpus as ``corpus.langs['oji']``.

Each item also has a member ``state`` whose value is a dict that maps
child types to lists. For example, one can also access the Ojibwe
language of a corpus as ``corpus.state['lang']['oji']``.

Each list has a member ``selected`` whose value is the currently selected
element. For example, if ``reg`` is the registry, then
the currently selected corpus is ``corpus = reg.state['corp'].selected``.
Additional selections can be accessed recursively, for example,
``lang = corpus.state['lang'].selected``.


Views
-----

A View is associated with a displayable Page in the UI. As mentioned
above, each item has a member ``views`` containing the available
views, and each view has a member ``view_of`` pointing to the item.
