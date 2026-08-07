
Pseudo-projective parsing
*************************

Pseudo-projective parsing involves a transformation applied to a set
of CoNLL sentences, and an inverse transformation applied to the
output of the parser.

The transformation converts the stemma to a projective stemma.
Nonprojectivity arises exactly when we have two crossing arcs, instead
of proper nesting.

Toplevel
--------

Stats
.....

The function print_stats() runs the projectivizer and reverter
on a list of sentences, and reports the results.  For example:::

   >>> from seal.nlp.dp.nnproj import print_stats
   >>> from seal.data import dep
   >>> print_stats(dep.sents('dan.orig', 'test'))
   Projective:       280 / 322 (86.956522%)
   Not projective:   42 / 322 (13.043478%)
   
   Not projective:
     Revertible:     39 / 42 (92.857143%)
     Not revertible: 3 / 42 (7.142857%)
   
   Revertible:
      1 lifts:    33
      2 lifts:     3
      3 lifts:     1
      4 lifts:     2
   
   Not revertible:
      1 lifts:     1
      2 lifts:     2

Nivre & Nilsson's algorithm
...........................

An arc (*g,d*) is defined to be nonprojective just in case it crosses
another arc *(g',d')* and *g'* dominates *g*.
Find the shortest nonprojective arc *(g,d)*,
breaking ties in favor of leftmost arcs.  Lift (*g,d*) by replacing it with
(*h,d*), where *h* is the governor of *g*.  Continue
until there are no nonprojective arcs.

Functions
.........

Let us use the following sentence as a running example::

   >>> from seal.core.config import ex
   >>> from seal.nlp.dep import conll_sents
   >>> s = next(conll_sents(ex.depsent2))
   >>> print(s)
   0 *root* _   _     _ _
   1 a      pos a/pos A 2
   2 b      pos b/pos B 4
   3 c      pos c/pos C 2
   4 d      pos d/pos D 0
   5 e      pos e/pos E 7
   6 f      pos f/pos F 3
   7 g      pos g/pos G 0
   8 h      pos h/pos H 7
   >>> govrs = s.column('govr')

The following functions provided by seal.depparse apply to
governor lists.

**Dominates** determines whether a given word dominates
another.  Domination is reflexive and transitive::

   >>> from seal.nlp.dp.nnproj import dominates
   >>> dominates(4, 1, govrs)
   True
   >>> dominates(4, 5, govrs)
   False

**Is nonproj** determines whether an arc is nonprojective or
not.  An arc (*g,d*) is defined to be nonprojective just in case any
word between *g* and *d* (exclusive) has a governor that is outside
the range (*g,d*)::

   >>> from seal.nlp.dp.nnproj import is_nonproj
   >>> is_nonproj((3,6), govrs)
   True

**Has nonproj arcs** returns True if there are any
nonprojective arcs in the sentence::

   >>> from seal.nlp.dp.nnproj import has_nonproj_arcs
   >>> has_nonproj_arcs(govrs)
   True

**Nonproj arcs** returns an iterator over the nonprojective
arcs in the sentence::

   >>> from seal.nlp.dp.nnproj import nonproj_arcs
   >>> list(nonproj_arcs(govrs))
   [(7, 5), (3, 6)]

**Next nonproj arc** returns the nonprojective arc with the
smallest span.  It breaks ties in favor of the leftmost arc::

   >>> from seal.nlp.dp.nnproj import next_nonproj_arc
   >>> next_nonproj_arc(govrs)
   (7, 5)

Projectivizer
-------------

Projectivizer functions
.......................

**Projectivize** takes either a sentence or iterator over
sentences, and returns the same type of object::

   >>> from seal.nlp.dp.nnproj import projectivize
   >>> ps = projectivize(s)
   >>> print(ps)
   0 *root* _   _     _   _
   1 a      pos a/pos A   2
   2 b      pos b/pos B   4
   3 c      pos c/pos C   2
   4 d      pos d/pos D   0
   5 e      pos e/pos G|E 0
   6 f      pos f/pos C|F 0
   7 g      pos g/pos G   0
   8 h      pos h/pos H   7

The return value is a copy; the original sentence is not modified.
The projectivizer only modifies non-projective arcs, so if the
original sentence is already projective, the new sentence is identical
to the old.

**Revert** takes a projectivized sentence, or iterator over
sentences, and attempts to reconstruct the original::

   >>> from seal.nlp.dp.nnproj import revert
   >>> rs = revert(ps)
   >>> rs == s
   True

**Stats** takes a sentence or an iterator over sentences.  For
a single sentence, it projectives and then attempts to revert the sentence.
It then returns a pair (*rev, nlifts*) where *rev*
is either 'revertible' or 'not-revertible' and *nlifts*
is the number of lifts performed during projectivization.  (Zero lifts
means that the original was already projective.)
For example:::

   >>> from seal.nlp.dp.nnproj import stats
   >>> stats(s)
   ('revertible', 4)

For a list of sentences, stats() returns a table
mapping the stats produced for single sentences to the list of
indices of sentences that have those stats.  (Note that it uses
*sent*.index(), not the actual position of the sentence in
the input list.)::

   >>> sents = dep.sents('dan.orig', 'test')
   >>> tab = stats(sents)
   >>> for (k,v) in sorted(tab.items()):
   ...     print(k, len(v))
   ...
   ('not-revertible', 1) 1
   ('not-revertible', 2) 2
   ('revertible', 0) 280
   ('revertible', 1) 33
   ('revertible', 2) 3
   ('revertible', 3) 1
   ('revertible', 4) 2
   >>> tab['not-revertible', 2]
   [131, 198]

Projectivizer implementation
............................

A Projectivizer implements the Nivre & Nilsson algorithm::

   >>> from seal.nlp.dp.nnproj import Projectivizer
   >>> p = Projectivizer()

It implements the following methods.

**Set sent** sets p.orig to a given sentence.  It
initializes p.govrs and p.roles to be copies of the
corresponding columns of the sentence.  It initializes p.lifted
to be a list containing False for each word in the sentence.
And it initializes p.nlifts to 0::

   >>> p.set_sent(s)
   >>> print(p)
   (2, 1) (4, 2) (2, 3) (0, 4) (7, 5) (3, 6) (0, 7) (7, 8)

Note that printing a projectivizer lists the arcs represented by its
govrs.

**Lift** takes an arc (*g,d*) as input.  It changes the
governor of *d* to be the governor of *g*::

   >>> p.lift((7,5))
   >>> print(p)
   (2, 1) (4, 2) (2, 3) (0, 4) (0, 5) (3, 6) (0, 7) (7, 8)

The governor of 7 is 0, so the arc (7,5) has been replaced with (0,5).

**Run** repeatedly
chooses the next arc and lifts it, until there are no more
nonprojective arcs.  It returns the resulting list of governors::

   >>> p.run()
   >>> print(p)
   (2, 1) (4, 2) (2, 3) (0, 4) (0, 5) (0, 6) (0, 7) (7, 8)

**Sentence** returns an updated CoNLL sentence::

   >>> print(p.sentence())
   0 *root* _   _     _   _
   1 a      pos a/pos A   2
   2 b      pos b/pos B   4
   3 c      pos c/pos C   2
   4 d      pos d/pos D   0
   5 e      pos e/pos G|E 0
   6 f      pos f/pos C|F 0
   7 g      pos g/pos G   0
   8 h      pos h/pos H   7

**Calling** a projectivizer as a function calls
set_sent() and run(), and then calls sentence()
to generate a projectivized sentence.  However, if the input sentence
already contains p-governors, it immediately returns the input
sentence.  To be precise, it returns a triple (*s,p,n*)
where *s* is the projectivized sentence, *p* is True if the
projectivized sentence is in fact the original sentence, and *n* is
the number of lifts performed, or None if the output is the
original sentence.

Reverter
--------

The function set_sent() initializes the reverter with a new
sentence::

   >>> from seal.nlp.dp.nnproj import Reverter
   >>> r = Reverter()
   >>> r.set_sent(ps)
   >>> print(r)
   0 None None
   1 2    A
   2 4    B
   3 2    C
   4 0    D
   5 0    G|E
   6 0    C|F
   7 0    G
   8 7    H

The method find_govr() is given arguments *root* and
*role*, and does a breadth-first search starting at *root*
to find a word whose role is *role.*::

   >>> r.find_govr(0, 'G')
   7

The method lower() is given a word *d* as input.
It calls find_govr() to find a new governor for *d*, and
reattaches *d* to the new governor::

   >>> r.lower(5)
   >>> print(r)
   0 None None
   1 2    A
   2 4    B
   3 2    C
   4 0    D
   5 7    E
   6 0    C|F
   7 0    G
   8 7    H

The method run() goes through the sentence from left to right.
It calls lower() on each word whose role contains a vertical
bar::

   >>> r.run()
   >>> print(r)
   0 None None
   1 2    A
   2 4    B
   3 2    C
   4 0    D
   5 7    E
   6 3    F
   7 0    G
   8 7    H

The method sentence() returns a sentence whose govrs and roles
are taken from the current state of the reverter.  Pgovrs and proles
are empty::

   >>> rs = r.sentence()
   >>> rs == s
   True

Calling the reverter as a function does set_sent() and
run(), and returns sentence().
