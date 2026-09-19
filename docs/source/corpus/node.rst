
Nodes
=====

The result of reading a corpus file is a single large python dict (a
cob). The primary desiderata are simplicity and non-redundancy.
For ease of use, the class Node provides a higher-level
interface. Nodes may be "virtual" elements that do not stand
in one-one correspondence with the cobs.

There are three kinds of node:

 * An **item** is a node that is backed by a cob. It can be selected
   for viewing or editting in the UI.

 * A **view** is a particular view of an item. Each item has a
   member ``views`` containing a list of views, and each view has a
   member ``view_of``, which is an item.

 * A **list** is a node that represents a choice among options. The
   elements of the list are items.

The class Node is instantiated with a parent node

An Item has a *parent* and a *key*. It also has a direct pointer to
the *file*, to make it easy to save the file. The parent link allows
one to iterate over ancestors. The key is broken down into item_type
and identifier. Contextual methods corpus(), language(), text(), and
sentence() are provided, that simply ask the parent.

A Node is a specialization of Item that has an underlying cob, as well
as children and properties. It behaves like a list of children; the
children are also Nodes. All children have the same type: the children
of a corpus are languages, the children of languages are texts, and so on.
That means that some sub-cobs are not accessible as children. Nodes
that have such sub-cobs have special methods to access them.
Since the square-bracket operator is used to access a Node's children
by index, we do not use it to access properties. Instead, a Node
has a member *props* that behaves like a dict and gives access to
the properties by key.

Items that are not Nodes do not have a special type, but conceptually,
they represent alternative *views* of an
underlying Node. The Node that they are a view of is considered their
parent, but they are not technically one of its children. The method
x.node() returns x's parent, if x is a view, but it returns x itself,
if x is a Node.

Nodes and Items are intended as lightweight wrappers for cobs, for the
sake of convenience. They are created "on the fly" - every time one
accesses a child of a Node, a new instance Node instance representing
is created to represent the child.
For that reason, Nodes and Items are effectively immutable -
all changes are made on the underlying cobs. Any change to the cob has immediate
effect precisely because every property of a Node or Item is
(re)computed whenever it is accessed.

There is a Node subclass for each variety
of object in the corpus. Subclasses include ``Corpus``,
``Lang``, ``Rom``, ``Text``, ``Lexicon``, ``Trans``, ``Sent``,
``Form``, ``Xlexicon``, ``Xtext``, and ``Times``.
There is one Item subclass that is not a Node, namely, ``Toc``, and
one class that is neither a Node nor Item, namely ``Token``.
