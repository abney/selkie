
``selkie.dep`` — Dependency conversion
======================================

Overview
--------

The toplevel function for conversions among tree types
is ``convert()``.  It takes optional
arguments giving the type of ``input`` and the type of ``output``.
By default, ``input`` is ``'tree'`` and ``output`` is ``'efstemma'``.

>>> from selkie.tree import parse_tree
>>> t = parse_tree('(S (NP (Pron this))'
...                '   (VP (VBZ is)'
...                '       (NP (DT a) (NN test))))')
...
>>> from selkie.dep import convert
>>> print(convert(t))
0 *root* _    _ _    _
1 this   Pron _ _    2
2 is     VBZ  _ root 0
3 a      DT   _ _    4
4 test   NN   _ _    2


To see how heads are assigned, one can specify ``'headed'`` output:

>>> print(convert(t, output='headed'))
0   (S
1      (NP
2         (Pron:head this))
3      (VP:head
4         (VBZ:head is)
5         (NP
6            (DT a)
7            (NN:head test))))


Or if one prefers a dependency tree to a stemma:

>>> print(convert(t, output='dep'))
0   (VBZ:root
1      (Pron this)
        is
2      (NN
3         (DT a)
           test))


The legal types input and output types are:

``'tree'`` for an unheaded constituency tree,
``'headed'`` for a headed constituency tree,
``'dep'`` for a dependency tree,
``'stemma'`` for a ``Sentence`` possibly containing empty words,
``'efstemma'`` for an &epsilon;-free stemma.


These reflect the steps of the
conversion: ``mark_heads()`` converts an unheaded tree to a headed
tree, ``dependency_tree()`` converts a headed tree to a dependency
tree, ``stemma()`` converts a dependency tree to a stemma, and
``eliminate_epsilons()`` eliminates empty words.

All steps except the first are non-destructive.  If given an unheaded
tree as input, ``convert()`` makes a copy before calling
``mark_heads()``, unless the keyword argument ``destructive=True``
is provided.

The keyword arguments ``projections`` and ``reductions`` may
optionally be provided; they are passed directly to
``dependency_tree()``.


Usage
-----

The central function provided by ``selkie.dep`` is ``dependency_tree()``,
which converts a headed phrase-structure tree to a dependency tree.
(It signals an error if it encounters a headless node.)

>>> h = parse_tree('''
...     (S (NP:subj (Det the) (N:head dog))
...        (VP:head (V:head chased)
...                 (NP:obj (Det a) (N:head cat)))
...        (Adv:mod quickly))
... ''')
>>> from selkie.dep import dependency_tree
>>> d = dependency_tree(h)
>>> print(d)
0    (V:root
1       (N:subj
2          (Det the)
           dog)
        chased
3       (N:obj
4          (Det a)
           cat)
5       (Adv:mod quickly))


The function ``dependency_tree()`` takes two keyword arguments:
``projections`` and ``reductions``.  They are passed directly to
the ``tree()`` method of ``Projection``, which is discussed
below.

It should be noted that the dependency tree may contain empty nodes.
The conversion treats all terminal nodes alike, whether they have a
string or ``None`` as their value for ``.word``.

Projections
-----------

The ``dependency_tree()`` function works by converting the tree first to
its *projections,* where a projection is defined as a list of
nodes, each being the head of the previous.  There is one projection
for each leaf node.  For example, in the
tree *h* above, "the" has projection (Det), "dog" has
projection (NP, N), "chased" has projection (S, VP, V),
"a" has projection (Det), "cat" has projection (NP, N), and
"quickly" has projection (Adv).

The left dependents of a projection are defined to be the
concatenation of left dependents of the nodes it contains, from
outermost to innermost.
The right dependents are defined to be the concatenation of the right
dependents of the nodes, from innermost to outermost.  For example,
the only left dependent of (S, NP, V) is the subject NP, and its right
dependents are the object NP and the adverb.

The class ``Projection`` represents a projection.  One creates a
projection from a headed tree:

>>> from selkie.dep import Projection
>>> p = Projection(h)

This actually creates projections recursively for the entire tree.

**Nodes.**
The value of attribute ``nodes`` is the list of nodes that make up
the projection:

>>> p.nodes
[<Tree S ...>, <Tree VP ...>, <Tree V chased>]


**Ldeps, rdeps.**
The attributes ``ldeps`` and ``rdeps`` contain the left and right
dependents, converted to projections:

>>> p.ldeps
[<Projection NP N dog>]
>>> p.rdeps
[<Projection NP N cat>, <Projection Adv quickly>]


**Lr, parent, headsib.**
Each non-root projection has values for ``lr``, ``parent``, and
``headsib``, representing the configuration in which the root node
occurs in the original tree.  This configuration is called the
"reduction" represented by attaching the root of projection to its parent.
For example, the projection for the
subject NP occurs as a left dependent in S, with head child VP.
Accordingly:

>>> sp = p.ldeps[0]
>>> sp.lr
'L'
>>> sp.parent
<Tree S ...>
>>> sp.headsib
<Tree VP ...>

(For the root projection, all three attributes have the value ``None``.)

**Tree.**
The method ``tree()`` converts a projection into a dependency tree.
By default, the category of a projection is taken to be the part of
speech of the head node (that is, ``nodes[-1]``.cat), and the role
is the role (if any) of the root node (that is, ``nodes[0].role``).

There are two boolean keyword arguments that can be used to select
alternative definitions of category and role.  If ``projections`` is
true, then the category is the concatenation of all categories in the
projection.  For example:

>>> print(p.tree(projections=True))
0    (S_VP_V:root
1       (NP_N:subj
2          (Det the)
           dog)
        chased
3       (NP_N:obj
4          (Det a)
           cat)
5       (Adv:mod quickly))

If ``reductions`` is true, then the role is represented by a
``Reduction`` object, which prints out as
the concatenation of ``lr``, ``nodes[0].cat``, ``parent.cat``,
and ``headsib.cat``.  For example:

>>> print(p.tree(reductions=True))
0    (V:root
1       (N:'L_NP:subj_S_VP'
2          (Det:L_Det_NP_N the)
           dog)
        chased
3       (N:'R_NP:obj_VP_V'
4          (Det:L_Det_NP_N a)
           cat)
5       (Adv:'R_Adv:mod_S_VP' quickly))

One can specify both ``projections`` and ``reductions``, if desired.

Reduction
---------

The class ``Reduction`` represents the configuration, in the
original headed phrase structure tree, in which a dependent occurs.
It has four attributes:

``lr`` may be "``L``," for a dependent that precedes its
head sibling, or "``R``," for one that follows, or "``root``,"
for the root node.
``dep`` is the category of the dependent.
``parent`` is the category of the parent node.
``head`` is the category of the head sibling.


Stemmas and governor arrays
---------------------------

A dependency stemma is represented by a ``Sentence`` instance, which
contains ``Word`` instances representing the individual words of the
sentence.  A ``Sentence`` may itself have an ``index()``, which is
intended to represent its position in a collection of sentences such
as a treebank.  Otherwise, a ``Sentence`` is simply a list of
``Word`` instances.  The word at position 0 is a pseudo-word
representing the root.

To create a sentence with a known number of words, use ``make_sentence()``:

>>> from selkie.dep import make_sentence
>>> s = make_sentence(4, index='test')
>>> s[1].form = 'This'
>>> s[2].form = 'is'
>>> s[3].form = 'a'
>>> s[4].form = 'test'
>>> print(s)
0 *root* _ _ _ _
1 This   _ _ _ 0
2 is     _ _ _ 0
3 a      _ _ _ 0
4 test   _ _ _ 0

Alternatively, one can create an empty sentence and add words one at a
time.  (Note that an "empty" sentence does contain a ``*root*``
pseudo-word.)

>>> from selkie.dep import Sentence, Word
>>> s = Sentence()
>>> s.append(Word(form='hi'))
>>> s.append(Word(form='there'))
>>> print(s)
0 *root* _ _ _ _
1 hi     _ _ _ 0
2 there  _ _ _ 0

One can copy an existing word by using the ``copy()`` method:

>>> s[1].copy()
<Word None hi govr=0>

The copy is identical to the original except that its ``sent`` and
``index`` are both ``None``.

.. py:class:: selkie.dep.Sentence

   The methods of ``Sentence`` are as follows:

   .. py:method:: index()

      Returns the index of the sentence.

   .. py:method:: providence()

      Returns the index as a string, or ``None``.

   .. py:method:: __len__()

      Includes the root pseudo-word.

   .. py:method:: __iter__()

      Iterates over all words, including the root pseudo-word.

   .. py:method:: __getitem__(i)

      Returns the *i*-th word; the root pseudo-word is at 0.

   .. py:method:: words()

      Returns a list of word forms (strings), excluding
      the root pseudo-word.

   .. py:method:: nwords()

      Excludes the root pseudo-word.

   .. py:method:: cmp(s, other)

      Sentences are compared by comparing
      words from left to right until a difference is found.  The root
      pseudo-words are assumed identical, and are not included in the comparison.

   .. py:method:: append(w)

      Adds w (not a copy) to the list of words.

   .. py:method:: form(i)

      Returns the form of the *i*-th word.

   .. py:method:: cat(i)

      Returns the category of the *i*-th word.

   .. py:method:: cpos(i)

      Returns the coarse category of the *i*-th word.
      This signals an error if the sentence is not a CoNLL sentence.

   .. py:method:: lemma(i)

      Returns the lemma of the *i*-th word.

   .. py:method:: morph(i)

      Returns the morph of the *i*-th word.

   .. py:method:: govr(i)

      Returns the governor of the *i*-th word.

   .. py:method:: role(i)

      Returns the role of the *i*-th word.

   .. py:method:: column(c)

      Returns the column named *c*, which
      should be one of ``'form'``, ``'cat'``, ``'lemma'``, ``'morph'``,
      ``'govr'``, or ``'role'``.  The column is a list of values, one
      for each word.  It includes the root pseudo-word.

.. py:class:: selkie.dep.Word

   The members of ``Word`` are as follows:

   .. py:attribute:: index

      The position of the word in the sentence; the
      root pseudo-word has index 0.

   .. py:attribute:: form

      The printed form of the word.

   .. py:attribute:: cat

      The part of speech.  In sentences read from a
      CoNLL-format file, the cat is a pair (*cpos, fpos*).

   .. py:attribute:: lemma

      The lemma, i.e., the key to use for lexical access.

   .. py:attribute:: morph

      Morphological information.

   .. py:attribute:: govr

      The index of the governor.

   .. py:attribute:: role

      The role with respect to the governor.

   The methods of ``Word`` are:

   .. py:method:: __lt__(other)

      Comparison is done by comparing
      attribute values in the order ``form``, ``cat``, ``lemma``,
      ``morph``, ``govr``, ``role``.  The attribute ``index`` is
      intentionally omitted, with the consequence that words at different positions in
      the sentence may be equal.  The attribute ``cpos`` is also
      omitted; it is assumed that ``cpos``, if present, is uniquely
      determined by ``cat``.

   .. py:method:: tagged_string()

      Returns "form.cat".


Conversion to ``Sentence`` (stemma)
-----------------------------------

A stemma is a list of ``Word`` objects, one for each word in
the sentence.  The ``Word`` class represents a word as the
dependent in a dependency link.  The function ``stemma()`` converts
a dependency tree into a stemma.  For example:

>>> from selkie.dep import stemma
>>> s = stemma(d)
>>> print(s, end='')
0 *root*   _    _ _    _
1 the      Det  _ _    2
2 dog      N    _ subj 3
3 chased   V    _ root 0
4 a        Det  _ _    5
5 cat      N    _ obj  3
6 quickly  Adv  _ mod  3

The columns are: index, word, part of speech, lemma, role, and
governor.  The value for governor is the index of the governor, not
the governor itself.

One can access a stemma like a list:

>>> s[2]
<Word 2 dog/N:subj govr=3>
>>> s[2].role
'subj'
>>> s[2].govr
3
>>> s[3]
<Word 3 chased/V:root govr=0>

The length of the stemma is the number of words in the sentence plus
one for the root:

>>> len(s)
7

The element at index 0 is a pseudo-word representing the root of the
sentence.

>>> s[0]
<Word 0 *root*>

The method ``words()`` returns a list of word forms (strings)
excluding the root pseudo-word.

>>> s.words()
['the', 'dog', 'chased', 'a', 'cat', 'quickly']


Governor array
--------------

A very compact representation of a dependency tree is the
*governor array*.  This is simply a list of numbers representing,
for each word, the index of the governor of that word.

>>> from selkie.dep import governor_array
>>> governor_array(d)
[2, 3, 0, 5, 3, 3]

The argument to ``governor_array()`` may be either a stemma or
something that can be converted to a stemma using the function ``stemma()``.

``DepLists``
------------

A ``DepLists`` object behaves as a list of lists.  It is indexed by
word index *i*, and returns the list of indices of words dependent on
*i*.  For example, in our example ``Sentence s``, word 3 (*chased*)
has dependents 2 (*dog*), 5 (*cat*), and 6
(*quickly*).

>>> from selkie.dep import DepLists
>>> deps = DepLists(s)
>>> deps[3]
[2, 5, 6]
>>> len(deps)
7

The ``DepLists`` object prints out readably:

>>> print(deps)
[0] *root*
        root: [3] chased
[1] the
[2] dog
        None: [1] the
[3] chased
        subj: [2] dog
        obj: [5] cat
        mod: [6] quickly
[4] a
[5] cat
        None: [4] a
[6] quickly

It contains a pointer to the original sentence, which can be used for
access to the identity of the dependents, etc.

>>> deps.sentence[2].form
'dog'


Lemmatization
-------------

The Sentence method ``lemmatize()`` sets the ``lemma``, ``cpos``,
and ``morph`` attributes for each word.
The value for ``lemma`` is
the lemmatized word.  The module ``selkie.stemmer`` is used.
The value for ``cpos`` is the part of speech with inflection
stripped.  The known inflected tags are
``'VBZ'``, ``'VBG'``, ``'VBN'``, ``'VBP'``, ``'VBD'``,
``'NN'``, ``'NNS'``, and the lemmatized versions are ``'V'`` or
``'N'``.
The value for ``morph`` is set to one of:
``'3s'``, ``'ing'``, ``'en'``, ``'pl'``, ``'ed'``, ``'sg'``,
``'pl'``.

The method is destructive.  It
only works for English.



Eliminating epsilons
--------------------

The Sentence method ``eliminate_epsilons()`` eliminates empty words
(those whose form is ``None``).  It is possible for empty words to
have dependents.  Suppose word *w* has governor *g*, which is empty.
The new governor of *w* is defined to be its lowest non-empty
ancestor, where *ancestor* means the transitive closure of
*governor-of.* 

>>> h = parse_tree('''
...   (VP (V:head thought)
...       (CP (C:head)
...           (S
...              (NP:subj (Name:head John))
...              (VP:head (V:head left)))))
... ''')
>>> s = stemma(dependency_tree(h))
>>> print(s)
0 *root*  _    _ _    _
1 thought V    _ root 0
2 _       C    _ _    1
3 John    Name _ subj 4
4 left    V    _ _    2
>>> print(s.eliminate_epsilons())
0 *root*  _    _ _    _
1 thought V    _ root 0
2 John    Name _ subj 3
3 left    V    _ _    1

CoNLL Format
------------

To get the raw contents of a file in CoNLL dependency format, use
``selkie.io.iter_record_blocks()``.

>>> from selkie.io import iter_record_blocks
>>> from selkie.data import ex
>>> sent = next(iter_record_blocks(ex('depsent1')))
>>> sent[0]
['1', 'This', 'this', '_', 'pron', '_', '2', 'subj', '_', '_']

The fields are: index, form, lemma, cpos, fpos, morph, head, rel,
phead, prel.  The fields cpos, phead, and prel are considered
"extra" information: they are optional, whereas fpos, head, and rel
are obligatory.  (Head and rel are obligatory, but need not be
projective; phead and rel are optional, but must be projective.)
Missing fields are represented with a single underscore character.

.. py:function:: iter_sentences(fn)

   The function ``iter_sentences()`` reads a CoNLL-format file as a
   sequence of ``selkie.dep.Sentence`` instances.  It takes a filename as
   input, with an optional "``#proj``" or "``#std``" suffix.
   The function ``conll_sents()`` is a synonym.
   
   The mapping between
   the raw fields and the Sentence attributes is done as follows.  For
   each word, if both cpos and fpos are present, then the cat is fpos and
   ``cpos`` is added as an extra attribute.
   If only one is present, it becomes the cat.  If the
   filename ends in ``#proj``, the phead and prel are used; otherwise,
   the head and rel are used.  (The suffix "``#std``" selects head
   and rel, but that is also the default.)
   
   >>> from selkie.dep import iter_sentences
   >>> s = next(iter_sentences(ex('depsent1')))
   >>> print(s[1])
   <Word 1 This/pron:subj (this) govr=2>
   >>> s[1].cat
   'pron'
   
.. py:function:: load_sentences(fn)

   Returns a list rather
   than an iteration.

.. py:function:: save_sentences(sents, fn)

   Takes a list of sentences and a filename as input.

   >>> from tempfile import TemporaryDirectory
   >>> from os.path import join
   >>> from selkie.dep import save_sentences, load_sentences
   >>> with TemporaryDirectory() as dfn:
   ...     fn = join(dfn, 'sents')
   ...     save_sentences([s], fn)
   ...     sents = load_sentences(fn)
   ...     print(sents[0])
   ...
   0 *root* _    _    _       _
   1 This   pron this subj    2   
   2 is     vb   be   mv      0   
   3 a      dt   a    det     4   
   4 test   n    test prednom 2   

If one loads a sentence and then saves it, the result may differ from
the original.  Namely, if the original records contain cpos but not
fpos, the cpos will show up in the fpos position in the saved file.

Universal postag mapping
------------------------

Das and Petrov (2011) [3145] introduced a set of universal
part-of-speech tags that were subsequently used in the McDonald et
al. delexicalized parsers.  Petrov, Das & McDonald [3300]
describe a set of tag tables, which are installed in ``selkie.data``
as ``conll/2006/universal-pos-tags``.

.. py:function:: load_umap(fn)

   Loads a tag map from a file, returning
   a dict.  (If given a relative pathname, it expands it relative to the
   ``universal-pos-tags`` directory.)

   >>> from selkie.dep import load_umap
   >>> map = load_umap('da-ddt.map')
   >>> map['VA']
   'VERB'

.. py:function:: apply_umap(tagmap, sent)

   Takes a map and a sentence in which
   the word ``cat`` values are (``cpos, fpos``) pairs, and
   it changes the ``cat`` values to be ``map[fpos]``.

.. py:function:: umapped_sents(fn, tagmap)

   Takes a filename and a map,
   and generates a sequence of sentences in which the map has been
   applied to the parts of speech.  It takes an optional flag
   ``projective=True`` whose meaning is the same as for ``conll_sents()``.

   The following example assumes that one has downloaded the CoNLL
   2006 data and stored its location under the config key ``data.conll``::

      >>> from selkie.config import config
      >>> from os.path import expanduser, join
      >>> conll = expanduser(config['data']['conll'])
      >>> fn = join(conll, '2006', 'danish', 'ddt', 'train', 'danish_ddt_train.conll')
      >>> from selkie.dep import umapped_sents
      >>> s = next(umapped_sents(fn, map))
      >>> s[1].form
      'Samme'
      >>> s[1].cat
      'ADJ'
