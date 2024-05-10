
Corpora and treebanks
=====================

The Brown corpus
----------------

The module selkie.data.brown behaves like an NLTK corpus, and
indeed it dispatches to nltk.corpus.brown in most cases.
However, it provides an alternative reduced tagset::

   >>> from selkie.data import brown
   >>> brown.tagged_words(tagset='base')[:3]
   [('The', 'AT'), ('Fulton', 'NP'), ('County', 'NN')]

Contrast this with the default tagset::

   >>> brown.tagged_words()[:3]
   [('The', 'AT'), ('Fulton', 'NP-TL'), ('County', 'NN-TL')]

Functionality
.............

NLTK provides the Brown corpus, though the version in selkie.data.brown
is tweaked.  The two basic functions are::

   >>> brown.words()
   >>> brown.tagged_words()

The latter takes an optional argument tagset.  If absent or
equal to "original," the full Brown tags are returned.  If equal to
"base," the prefix FW- and the
suffixes (-NC, -TL, and -HL) are removed from the tags.
There are a few places where -T occurs in the original as an
error for -TL; these are also stripped.

One can also call the function brown.base() on a tag to strip
its prefixes and suffixes, if any.  In addition, the function
brown.ispunct() indicates whether a tag is a punctuation tag or
not, and brown.isproper() indicates whether a tag is a proper
name tag or not.

Both brown.words() and brown.tagged_words() can be called
with optional parameters categories or fileids, with the
same interpretation as in NLTK.

The Brown tagset
................

There are 188 base tags, which break down as follows:

 * NIL (1 tag)
 * Compound tags (96 tags)
 * Simple tags (91 tags)
    * Punctuation tags (9 tags)
    * Proper-noun tags (4 tags)
    * Regular word tags (78 tags)
       * Tags for unique lexical items (21 tags)
       * Closed-class tags (39 tags)
       * Open-class tags (18 tags)

**NIL.**
There are 157 tokens in the original that are tagged "NIL."
This appears to be simply a gap in the tagging.  They are not removed
from the output of stripped().

**Compound tags.**
The compound tags are for contracted word pairs; four of them are
actually contracted word triples.  They exclude possessives, inasmuch
as the possessive marker is not an independent word.  The majority of
contractions involve either the combination of a verb tag with
\*, which represents the contraction "n't";
or the combination of a noun or pronoun tag with a
verb or auxiliary tag.  There are, however, a fair number of other cases
as well.  The simple tags making up compound tags all occur
independently, with the exception of "PP," which occurs in a
compound tag but not standing alone.  It is probable that this is an
error for PPS or PPO, particularly since it occurs at the
end of a long tag that may have gotten truncated.

**Punctuation tags.**
Of the 91 simple tags, nine are punctuation tags::

   ' '' ( ) , -- . : ``

**Proper-noun tags.**
Four tags represent proper nouns::

   NP NP$ NPS NPS$

The tag NP includes titles such as "Mr." and "Jr.," as well
as place names, month names, and the like.  NPS includes
words like "Republicans."

**Unique lexical items.**
There are 21 tags that represent unique lexical items.  We ignore
spelling variation, nonstandard dialect forms, and foreign words.
A few of the possessive tags, namely DT$, JJ$,
AP$, CD$, RB$, appear on only one word each, but
those represent rare constructions or questionable tagging decisions,
and are listed elsewhere.

.. list-table::

   * - \*
     - *not*
   * - ABX
     - *both*
   * - BE
     - *be*
   * - BED
     - *were*
   * - BEDZ
     - *was*
   * - BEG
     - *being*
   * - BEM
     - *am*
   * - BEN
     - *been*
   * - BER
     - *are*
   * - BEZ
     - *is*
   * - DO
     - *do*
   * - DOD
     - *did*
   * - DOZ
     - *does*
   * - EX
     - *there*
   * - HV
     - *have*
   * - HVD
     - *had*
   * - HVG
     - *having*
   * - HVN
     - *had*
   * - HVZ
     - *has*
   * - TO
     - *to*
   * - WQL
     - *how, however*

**Closed-class tags.**
There are 39 closed-class tags:

Conjunctions

.. list-table::

   * - CC
     - *and, but, or, nor, either, yet, neither, plus, minus, though*
   * - CS
     - complementizers

Specifiers

.. list-table::

   * - ABL
     - *such, quite, rather*
   * - ABN
     - *all, half, many, nary*
   * - AP
     - *other, many, more, same, ...*
   * - AP$
     - *other's*
   * - AT
     - *the, a(n), no, every*
   * - DTI
     - *some, any*
   * - DTS
     - *these, those*
   * - DTX
     - *either, neither, one*
   * - DT
     - *this, that, each, another*
   * - DT$
     - *another's*
   * - QLP
     - *enough, indeed, still*

Numbers

.. list-table::

   * - CD
     - cardinal numbers
   * - CD$
     - *1960's, 1961's*
   * - OD
     - ordinal numbers

Pronouns

.. list-table::

   * - PPS
     - *he, it, she*
   * - PPSS
     - *I, they, we, you*
   * - PPO
     - *it, him, them, me, her, you, us*
   * - PP$
     - *his, their, her, its, my, our, your*
   * - PP$$
     - *his, mine, ours, yours, theirs, hers*
   * - PPL
     - *himself, itself, myself, herself, yourself, oneself*
   * - PPLS
     - *themselves, ourselves, yourselves*
   * - PN
     - *one; (some-, no-, any-, every-) + (-thing, -body)*
   * - PN$
     - *one's, anyone's, everybody's, ...*
   * - RN
     - *here, then, afar*

Interrogatives

.. list-table::

   * - WDT
     - *which, what, whichever, whatever*
   * - WPS
     - *who, that, whoever, what, whatsoever, whosoever*
   * - WPO
     - *whom, that, what, who*
   * - WP$
     - *whose, whosever*
   * - WRB
     - *when, where, how, why,* plus many variants

Other Closed Classes

.. list-table::

   * - MD
     - modals
   * - NR
     - adverbial nouns: days of the week, cardinal directions, etc.
   * - NRS
     - plural adverbial nouns
   * - NR$
     - possessive adverbial nouns
   * - QL
     - qualifiers (adverbs that modify quantifiers)
   * - IN
     - prepositions
   * - RP
     - particles
   * - UH
     - interjections

**Open-class tags.**
There are 18 open-class tags, of which two (JJ$ and RB$)
appear to be the result of phrasal use of the possessive, and should
probably be placed in the class of compound tags.

Nouns

.. list-table::

   * - NN
     - singular
   * - NNS
     - plural
   * - NN$
     - possessive
   * - NNS$
     - possessive plural

Verbs

.. list-table::

   * - VBZ
     - third-person singular
   * - VBD
     - past tense
   * - VB
     - uninflected form
   * - VBG
     - present participle
   * - VBN
     - past participle

Adjectives

.. list-table::

   * - JJ
     - positive
   * - JJR
     - comparative
   * - JJS
     - intrinsically superlative
   * - JJT
     - morphologically superlative
   * - JJ$
     - *Great's*

Adverbs

.. list-table::

   * - RB
     - adverb
   * - RBR
     - comparative
   * - RBT
     - superlative
   * - RB$
     - *else's*

The Penn Treebank
-----------------

Another source of trees is the Penn treebank, represented by the module
ptb.  It contains functions to access the Penn Treebank and
its parts.

One may specify in the Selkie configuration file
the pathname for the contents of LDC99T42.

Fileids and categories
......................

The treebank consists of 2312 files divided into 25 sections.
There is a traditional division into train, test, dev
train, dev test, and reserve test parts:

.. list-table::
   :header-rows: 1

   * - Division
     - Sections
     - Files
   * - dev_train
     - 00-01
     - 0-198
   * - train
     - 02-21
     - 199-2073
   * - reserve_test
     - 22
     - 2074-2156
   * - test
     - 23
     - 2157-2256
   * - dev_test
     - 24
     - 2257-2311

The functions follow the conventions of the NLTK corpus readers.  The
function fileids() returns a list of file identifiers, which are
actually numbers in the range [0,2312).  One can also specify one or
more categories.  Category names are either WSJ section names, in the
form '00', '01', up to '24', or one of the
following: 'train', 'test', 'dev_train',
'dev_test', 'reserve_test'.  One can get a list of the
fileids in a given category, or the categories that a given file
belongs to::

   >>> from selkie.data import ptb
   >>> len(ptb.fileids())
   2312
   >>> len(ptb.fileids(categories='train'))
   1875
   >>> ptb.fileids('dev_train')[-5:]
   [194, 195, 196, 197, 198]
   >>> ptb.categories(0)
   ['00', 'dev_train']
   >>> ptb.categories(2311)
   ['24', 'dev_test']
   >>> for c in sorted(ptb.categories()):
   ...     if c.islower():
   ...         print(c, len(ptb.fileids(c)))
   ... 
   dev_test 55
   dev_train 199
   reserve_test 83
   test 100
   train 1875

Filenames
.........

One can obtain the filename for a given fileid::

   >>> ptb.orig_filename(199)[-15:]
   '02/wsj_0200.mrg'

Reverse look-up is also possible::

   >>> ptb.orig_to_fileid('0200')
   199

The reverse look-up table is loaded the first time that
orig_to_fileid() is called.

Trees
.....

The method trees() returns a list of all the individual
trees in the treebank or a slice of it::

   >>> trees = ptb.trees(0)
   >>> print(trees[0])
   0   (
   1      (S
   2         (NP:SBJ
   3            (NP
   4               (NNP Pierre)
   5               (NNP Vinken))
   6            (, ,)
   ...
   >>> len(ptb.trees(categories='dev_test'))
   1346

There is also a function iter_trees() that returns
iterations rather than lists.

Empty nodes
...........

In the original treebank, typical empty nodes look like this::

   (NP-SBJ (-NONE- *-1) )
   (SBAR (-NONE- 0) 
      (S (-NONE- *T*-1) ))

We omit "-NONE-" and treat "*," "0," or
"*T*" as the category.  The word and children are both None.
For example::

   >>> trees = ptb.trees(categories='dev_test')
   >>> tree = trees[30]
   >>> np = tree[18]
   >>> print(np)
   0   (NP:SBJ
   1      (*T* &amp;1))
   >>> t = np.children[0]
   >>> t.cat
   '*T*'
   >>> t.word
   ''
   >>> tree = trees[86]
   >>> s1 = tree[36]
   >>> print(s1)
   0    (SBAR
   1       (0)
   2       (S
   3          (*T* &amp;1)))
   >>> s1.children[0].cat
   '0'
   >>> s = s1.children[1]
   >>> s.children[0].cat
   '*T*'

Methods
.......

The module ptb is summarized in the following table.
The optional *f* and *c* are optional and can also be
provided by keyword: fileids and categories,
respectively.

 * fileids(c) — The file IDs in categories *c*

 * categories(f) — The categories for fileids *f*

 * trees(f,c) — The trees in the given files/categories

 * words(f,c) — The words

 * sents(f,c) — Sentences (lists of words)

 * raw_sents(f,c) — Sentence strings

 * abspath(f) — The absolute pathname for the fileid

 * text_filename(f) — Pathname for the text file

 * orig_filename(f) — The original pathname

 * fileid_from_orig(o) — Convert original ID (4 digits)

 * text_files(f,c) — List of text filenames

 * orig_files(f,c) — List of original filenames

The function fileid_from_orig() takes an original file
identifier.  It strips a trailing file suffix, if any, and then
ignores everything except the last four characters, which should be
digits, such as "0904," which represents file 04 in WSJ section 09.
Accordingly, "parsed/mrg/wsj/09/wsj_0904.mrg,"
"wsj_0904.mrg," and simply "0904" are
treated as synonymous.

Statistics
..........

Bikel [2767] reports a number of statistics for the standard
training slice (sections 02--21) of the Penn Treebank.
We can compute our own statistics and compare, as follows.  (Be warned, the calls that iterate
over trees take on the order of minutes to return.)

**Number of sentences.**
Bikel counts 39,832 sentences.  Our count agrees::

   >>> count(ptb.trees(categories='train'))
   39832

**Number of word tokens.**
Bikel counts 950,028 word tokens (not including null elements).  Our
count agrees::

   >>> count(n for t in ptb.trees(categories='train')
   ...             for n in t.nodes()
   ...                 if n.isword())
   950028
   >>> count(ptb.words(categories='train'))
   950028

**Number of word types.**
Bikel counts 44,114 unique words (not including null elements).  Our
count is slightly higher.  I do not know why there is a discrepancy::

   >>> len(set(n.word for t in ptb.trees(categories='train')
   ...                    for n in t.nodes()
   ...                        if n.isword()))
   44389
   >>> len(set(ptb.words(categories='train')))
   44389

**Number of words with a count greater than 5.**
Bikel reports that 10,437 word types occur 6 times or more.  Our count
is again a little higher::

   >>> count(w for w in wcts if wcts[w] >= 6)
   10530

**Number of interior nodes.**
Bikel reports 904,748 brackets.  Our count is quite a bit lower::

   >>> count(n for t in ptb.trees(categories='train')
   ...             for n in t.nodes()
   ...                 if n.isinterior())
   792794

**Number of nonterminal categories.**
Bikel reports 28 basic nonterminals, excluding roles ("function
tags," in his terms) and indices.
Including roles and indices, he reports 1184 full nonterm labels::

   >>> ntcats = set(n.cat for t in ptb.trees(categories='train')
   ...                        for n in t.nodes()
   ...                            if n.isinterior())
   >>> len(ntcats)
   27
   >>> sorted(ntcats)
   [ADJP, ADVP, CONJP, FRAG, INTJ, LST, NAC, NP, NX, PP, PRN, PRT,
   PRT|ADVP, QP, RRC, S, SBAR, SBARQ, SINV, SQ, UCP, VP, WHADJP, WHADVP,
   WHNP, WHPP, X]

It is not clear what Bikel's extra category is.  Possibly he went
beyond the training data.

Actually, we should probably replace "PRT|ADVP" with either PRT
or ADVP.  That would leave only 26 categories.

**Number of terminal categories.**
Bikel reports 42 unique part of speech tags.  We count 55::

   >>> parts = set(n.cat for t in ptb.trees(categories='train')
   ...                       for n in t.nodes()
   ...                           if n.isleaf())
   >>> len(parts)
   55
   >>> sorted(parts)
   [#, $, '', *, *?*, *EXP*, *ICH*, *NOT*, *PPA*, *RNR*, *T*, *U*, ,,
     -LRB-, -RRB-, ., 0, :, CC, CD, DT, EX, FW, IN, JJ, JJR, JJS, LS, MD,
     NN, NNP, NNPS, NNS, PDT, POS, PRP, PRP$, RB, RBR, RBS, RP, SYM, TO,
     UH, VB, VBD, VBG, VBN, VBP, VBZ, WDT, WP, WP$, WRB, ``]

Eliminating empty leaves reduces the number of parts of speech to 45::

   >>> parts = set(n.cat for t in ptb.trees(categories='train')
   ...                       for n in t.nodes()
   ...                           if n.isleaf() and not n.isempty())
   >>> len(parts)
   45
   >>> sorted(parts)
   [#, $, '', ,, -LRB-, -RRB-, ., :, CC, CD, DT, EX, FW, IN, JJ, JJR,
     JJS, LS, MD, NN, NNP, NNPS, NNS, PDT, POS, PRP, PRP$, RB, RBR, RBS,
     RP, SYM, TO, UH, VB, VBD, VBG, VBN, VBP, VBZ, WDT, WP, WP$, WRB, ``]

**Number of roles.**
Bikel does not count roles separately.  We can::

   >>> roles = set(imap(Node.role, trn.nodes()))
   >>> roles
   set([TMP, DIR, PRP-CLR, SBJ-TTL, LOC-HLN, TPC, CLR-TPC, CLF,
   CLF-TPC, PUT-TPC, PRD-TPC, NOM-TPC, LGS, PRP-TPC, PRD-TTL,
   TPC-TMP, MNR, TPC-PRD, LOC-PRD-TPC, DIR-PRD, LOC-TMP, SBJ,
   TMP-TPC, MNR-PRD, HLN, MNR-CLR, BNF, LOC-MNR, PRD-LOC-TPC,
   LOC-CLR, TTL, NOM-SBJ, CLR-LOC, NOM, DIR-TPC, TPC-CLR, PRD-TMP,
   CLR, TTL-PRD, TMP-CLR, TMP-HLN, LOC-TPC-PRD, PRP-PRD, LOC-TPC,
   None, LOC-CLR-TPC, VOC, EXT, MNR-TMP, PRD, NOM-LGS, CLR-TMP,
   TMP-PRD, ADV, DTV, NOM-PRD, TTL-SBJ, TPC-LOC-PRD, LOC-PRD,
   PRD-LOC, ADV-TPC, CLR-MNR, DIR-CLR, PUT, TTL-TPC, PRP, LOC,
   CLR-ADV, MNR-TPC])
   >>> len(roles)
   69

Categories
..........

The categories occurring in the treebank can be divided into three
groups: nonterminal categories, parts of speech, and empty categories.

**Nonterminal categories** label interior nodes, that is,
nodes that have children.  (In the treebank, no interior nodes are
labeled with words.)
There are 28 nonterminal categories, as follows.

 * ADJP — Adjective phrase

 * ADVP — Adverb phrase

 * ADVP|PRT — Indecision 

 * CONJP — Conjunction phrase

 * FRAG — Fragment

 * INTJ — Interjection

 * LST — List enumerator

 * NAC — Not a constituent

 * NP — Noun phrase

 * NX — NP head fragment

 * PP — Prepositional phrase

 * PRN — Parenthetical

 * PRT — Particle 

 * PRT|ADVP — Indecision

 * QP — Quantifier phrase

 * RRC — Reduced relative clause

 * S — Sentence

 * SBAR — Subordinate clause

 * SBARQ — Interrogative clause

 * SINV — Inverted sentence

 * SQ — Interrogative sentence

 * UCP — Unlike coord'd phrase 

 * VP — Verb phrase

 * WHADJP — Wh adjective phrase

 * WHADVP — Wh adverb phrase

 * WHNP — Wh noun phrase

 * WHPP — Wh prepositional phrase

 * X — Unknown, unbracketable

**Parts of speech** label nodes that have words.  There are 45 parts
of speech, as follows.

 * # — Monetary sign

 * $ — U.S. dollars

 * '' — Close quotes

 * , — Comma

 * -LRB- — Left parenthesis

 * -RRB- — Right parenthesis

 * . — Period

 * : — Colon

 * CC — Coordinator

 * CD — Number

 * DT — Determiner

 * EX — Existential *there*

 * FW — Foreign word

 * IN — Preposition

 * JJ — Adjective

 * JJR — Comparative adjective

 * JJS — Superlative adjective

 * LS — List enumerator

 * MD — Modal

 * NN — Common noun

 * NNP — Proper noun

 * NNPS — Plural proper noun

 * NNS — Plural common noun

 * PDT — ?

 * POS — Possessive marker

 * PRP — Personal pronoun

 * PRP$ — Possessive pronoun

 * RB — Adverb

 * RBR — Comparative adverb

 * RBS — Superlative adverb

 * RP — Particle

 * SYM — Symbol

 * TO — Infinitival *to*

 * UH — Interjection

 * VB — Uninflected verb

 * VBD — Verb + *ed*

 * VBG — Verb + *ing*

 * VBN — Verb + *ed/en*

 * VBP — Plural verb

 * VBZ — Verb + *-s*

 * WDT — Wh determiner

 * WP — Wh pronoun

 * WP$ — *whose*

 * WRB — Wh adverb

 * \`` — Open quotes

**Empty categories** label empty leaf nodes, that is, nodes that
have neither children nor words.  There are 10 empty categories,
listed in the following table.

 * * — PRO or trace of NP-movement; preterminal cat is NP

 * *?* — Elipsis 

 * *EXP* — Pseudo-attachment: extraposition

 * *ICH* — Pseudo-attachment: "interpret constituent
    here" (discontinuous dependency)

 * *NOT* — "Anti-placeholder" in template gapping

 * *PPA* — Pseudo-attachment: "permanent predictable ambiguity" 

 * *RNR* — Pseudo-attachment: right-node raising

 * *T* — Trace of wh-movement 

 * *U* — Unit 

 * 0 — Null complementizer

NX is generally
used in coordinate structures.  It may be used for N-bar
coordination: "the [<sub>NX</sub> red book] and
[<sub>NX</sub> yellow pencils]."  It is also
used in non-constituent coordination structures such as "20 thin
[<sub>NX</sub>] and 10 fat [<sub>NX</sub>]
[<sub>NX</sub> dogs],"
where "dogs" is treated as a right-node raised node.  It is
also used for book/movie titles that have premodifiers.

Lists of the categories are found in the following variables::

   >>> len(ptb.nonterminal_categories)
   28
   >>> len(ptb.parts_of_speech)
   45
   >>> len(ptb.empty_categories)
   10

These lists were constructed using
the function collect_categories().
It returns a list containing three sets: nonterminal categories, parts
of speech, and empty categories.  A category is defined to be
nonterminal if it appears on a node with children, a part of speech if
it appears on a node with a word, and an empty category otherwise.
Note that the empty string is included as an extra nonterminal category: there
are some nonterminal nodes (root nodes) without a category.

Roles
.....

The roles that occur in the PTB are listed in the following table.

 * ADV — Adverbial (form vs function) — Used on NP or SBAR, but not ADVP or PP.  Subsumes
   more-specific adverbial tags.

 * BNF — Benefactive (adverbial) — May be used on indirect object.

 * CLF — Cleft (misc) — *It* clefts.  Marks the whole sentence; not
   actually a role.

 * CLR — Closely related (misc) — Intermediate between argument and modifier.

 * DIR — Direction (adverbial) — May be multiple: *from, to.*

 * DTV — Dative (grammatical role) — Only used if
   there is a double-object variant.  Also ablative meaning: ask a question [of X].  But anything
   with *for* is BNF.  Not used on indirect object!  

 * EXT — Extent (adverbial) — Distance, amount.  Not for obligatory
   complements, e.g. of *weigh.*

 * HLN — Headline (misc) — Marks the whole phrase; not actually a role.

 * LGS — Logical subject (grammatical role) — The NP in a passive by-phrase.

 * LOC — Locative (adverbial)

 * MNR — Manner (adverbial)

 * NOM — Nominal (form vs function) — Marks headless relatives behaving as
   substantives.  Not actually a role.  Co-occurs with SBJ and other argument roles.

 * PRD — Predicate (grammatical role) — Any predicate that is not a
   VP.  Also, the *so* in *do so.*

 * PRP — Purpose or reason (adverbial)

 * PUT — Locative of *put* (grammatical role)

 * SBJ — Subject (grammatical role)

 * TMP — Temporal (adverbial)

 * TPC — Topicalized (grammatical role) — Only if there is a trace or resumptive
   pronoun after the subject.

 * TTL — Title (misc) — The title of a work, implies NOM.  Marks the
   whole phrase; not actually a role.

 * VOC — Vocative (grammatical role)

Perseus Latin and Greek Treebanks
---------------------------------

The module perseus contains small Latin and Greek treebanks from
Project Perseus.  The main method for these treebanks is stemmas(),
which returns an iterator over the stemmas in the treebank.
(Yes, "stemmata" is the correct plural, but it is rather
pedantic, so we have anglicized)::

   >>> from selkie.data import perseus
   >>> stemmas = list(perseus.latin.stemmas())
   >>> len(stemmas)
   3473
   >>> print(stemmas[0])
   0 *root*  _         _       _    _
   1 In      r-------- in1     AuxP 4
   2 nova    a-p---na- novus1  ATR  7
   3 fert    v3spia--- fero1   PRED 8
   4 animus  n-s---mn- animus1 SBJ  2
   5 mutatas t-prppfa- muto1   ATR  6
   6 dicere  v--pna--- dico2   OBJ  2
   7 formas  n-p---fa- forma1  OBJ  5
   8 corpora n-p---na- corpus1 OBJ  0

Dependency treebanks
--------------------

Accessing datasets
..................

A dataset has a **language** and a **version**.
Languages are specified as ISO 639-3 codes.
There are currently four different versions, as follows.
The original CoNLL treebanks from
the 2006 shared task have version orig.  
Datasets converted to the Das-Petrov universal tagset (DPU) have version
umap.
The Universal Dependency Treebank (UDT) with standard encoding has version uni.
The Universal Dependency Treebank with content-head encoding (ch).
The Penn Treebank (PTB) converted to dependencies using my adaptation of the
Magerman-Collins (MC) rules has version dep.  The same converted
to the Das-Petrov tagset has version umap.
The following table lists the currently available datasets.
(DPU = Das-Petrov Universal tagset;
UDT = Universal Dependency Treebank.}

.. list-table::
   :header-rows: 1

   * - Name
     - Lg
     - Ver
     - Description
   * - arb.orig
     - arb
     - orig
     - CoNLL-2006 Arabic
   * - arb.umap
     - arb
     - umap
     - CoNLL-2006 + DPU, Arabic
   * - bul.orig
     - bul
     - orig
     - CoNLL-2006 Bulgarian
   * - bul.umap
     - bul
     - umap
     - CoNLL-2006 + DPU, Bulgarian
   * - ces.orig
     - ces
     - orig
     - CoNLL-2006 Czech
   * - ces.umap
     - ces
     - umap
     - CoNLL-2006 + DPU, Czech
   * - dan.orig
     - dan
     - orig
     - CoNLL-2006 Danish
   * - dan.umap
     - dan
     - umap
     - CoNLL-2006 + DPU, Danish
   * - deu.ch
     - deu
     - ch
     - UDT, content-head, German
   * - deu.orig
     - deu
     - orig
     - CoNLL-2006 German
   * - deu.umap
     - deu
     - umap
     - CoNLL-2006 + DPU, German
   * - deu.uni
     - deu
     - uni
     - UDT, German
   * - eng.dep
     - eng
     - dep
     - Penn Treebank, MC heads
   * - eng.umap
     - eng
     - umap
     - Penn Treebank, MC heads + DPU
   * - fin.ch
     - fin
     - ch
     - UDT, content-head, Finnish
   * - fra.ch
     - fra
     - ch
     - UDT, content-head, French
   * - fra.uni
     - fra
     - uni
     - UDT, French
   * - ind.uni
     - ind
     - uni
     - UDT, Indonesian
   * - ita.uni
     - ita
     - uni
     - UDT, Italian
   * - jpn.uni
     - jpn
     - uni
     - UDT, Japanese
   * - kor.uni
     - kor
     - uni
     - UDT, Korean
   * - nld.orig
     - nld
     - orig
     - CoNLL-2006 Dutch
   * - nld.umap
     - nld
     - umap
     - CoNLL-2006 + DPU, Dutch
   * - por.orig
     - por
     - orig
     - CoNLL-2006 Portuguese
   * - por.umap
     - por
     - umap
     - CoNLL-2006 + DPU, Portuguese
   * - por.uni
     - por
     - uni
     - UDT, Portuguese
   * - slv.orig
     - slv
     - orig
     - CoNLL-2006 Slovenian
   * - slv.umap
     - slv
     - umap
     - CoNLL-2006 + DPU, Slovenian
   * - spa.ch
     - spa
     - ch
     - UDT, content-head, Spanish
   * - spa.orig
     - spa
     - orig
     - CoNLL-2006 Spanish
   * - spa.umap
     - spa
     - umap
     - CoNLL-2006 + DPU, Spanish
   * - spa.uni
     - spa
     - uni
     - UDT, Spanish
   * - swe.ch
     - swe
     - ch
     - UDT, content-head, Swedish
   * - swe.orig
     - swe
     - orig
     - CoNLL-2006 Swedish
   * - swe.umap
     - swe
     - umap
     - CoNLL-2006 + DPU, Swedish
   * - swe.uni
     - swe
     - uni
     - UDT, Swedish
   * - tur.orig
     - tur
     - orig
     - CoNLL-2006 Turkish
   * - tur.umap
     - tur
     - umap
     - CoNLL-2006 + DPU, Turkish

The **name** of a dataset is language-dot-version, for example dan.orig.
The function dataset() gives access to a dataset by name::

    >>> from selkie.data import dep
    >>> dep.dataset('dan.orig')
    <Dataset dan.orig>

The function datasets() gives access to sets of datasets.
Language or version may be specified::

   >>> dep.datasets(lang='dan')
   [<Dataset dan.orig>, <Dataset dan.umap>]
   >>> len(dep.datasets(version='orig'))
   18
   >>> len(dep.datasets())
   52

Dataset instances
.................

The class Dataset represents a treebank.  There are two
specializations, UMappedDataset and FilterDataset.
Each dataset has a name, a description, a language represented as an ISO 639-3 code,
and a version::

   >>> ds = dep.dataset('dan.orig')
   >>> ds.name
   'dan.orig'
   >>> ds.desc
   'Danish, CoNLL-2006'
   >>> ds.lang
   'dan'
   >>> ds.version
   'orig'

Simple datasets also have
a training file pathname, a test file pathname, and (sometimes) a dev
file pathname.  (To be precise, datasets in the uni
and ch collections have a dev file pathname, but orig
datasets do not.)  The pathnames are also available for umapped
datasets, but the files contain the original (unmapped) trees.
Filter datasets do not have pathnames::

   >>> ds.train[ds.train.find('conll'):]
   'conll/2006/danish/ddt/train/danish_ddt_train.conll'
   >>> ds.test[ds.test.find('conll'):]
   'conll/2006/danish/ddt/test/danish_ddt_test.conll'
   >>> ds.dev
   >>>

Sentences
.........

A dataset instance has a sents() method that generates
sentences for a specified **section** of the treebank.
All treebanks have 'train' and 'test' sections.
In addition, uni and ch datasets have a 'dev' section,
and the English datasets have 'dev_train', 'dev_test',
and 'reserve_test' sections::

   >>> sents = list(ds.sents('train'))
   >>> len(sents[0])
   14

A convenience function called sents() is also available to retrieve the sentences for
a particular segment of a dataset directly::

   >>> sents = list(dep.sents('dan.orig', 'train'))

A sentence can be viewed as a list of records.  Word~0 is 
always the root pseudo-word.  "Real" words start at position 1.
The length of the sentence includes the root, so the last valid index
is the length minus one::

   >>> s = sents[0]
   >>> s[0]
   <Word 0 *root*>
   >>> s[1]
   <Word 1 Samme/AN:ROOT (/A.degree=po...) govr=0>
   >>> s[13]
   <Word 13 ./XP:pnct (/X) govr=1>

The Sentence and Word classes were discussed earlier.
Each record is represented by a Word instance, with ten
fields: i, form, lemma, cpos,
cat, morph, govr, role, pgovr, and prole.
The field cpos represents the coarse part of speech, and
cat represents the fine part of speech.  The fields pgovr
and prole represent the word's governor and role in the
projective stemma.  They may not be available.  The fields govr
and role are always available, but they are not guaranteed to be
projective.

All fields except i, govr, and pgovr are
string-valued.  If not available, their value is the empty string.
The values for i, govr, and pgovr are integers.  If
they are not available, their value is None.
The fields i and govr are always available, except that
word 0 has no govr.

The values for govr and pgovr can be used used as
an index into the sentence, with the value 0 representing the root.

One can get just a list of word forms (strings) using the method
words().  This provides suitable input for a standard parser.
The root pseudo-word is not included.
The method nwords() returns the number of words excluding the root::

   >>> ws = s.words()
   >>> ws[:3]
   ['Samme', 'cifre', ',']
   >>> len(ws)
   13
   >>> s.nwords()
   13

Column-major view
.................

A sentence provides separate methods for each of the word attributes,
indexed by the word number, with 0 being the root pseudo-word::

   >>> s.form(0)
   '*root*'
   >>> s.form(1)
   'Samme'
   >>> s.form(13)
   '.'

The attributes are as listed above: form, lemma, cpos,
cat, morph, govr, role, pgovr, and prole::

   >>> s.form(2)
   'cifre'
   >>> s.lemma(2)
   ''
   >>> s.cpos(2)
   'N'
   >>> s.cat(2)
   'NC'
   >>> s.morph(2)
   'gender=neuter|number=plur|case=unmarked|def=indef'
   >>> s.govr(2)
   1
   >>> s.role(2)
   'nobj'

Word forms need not be ascii::

   >>> from selkie.cld.seal.misc import as_ascii
   >>> as_ascii(s.form(12))
   'v{e6}rtsnation'

Without as_ascii, the form would print as "v&aelig;rtsnation."

One can fetch a column as a tuple using the method column()::

   >>> g = s.column('govr')
   >>> g[:5]
   (None, 0, 1, 1, 7)

Creating a sentence
...................

If desired, one can create a Sentence as follows::

   >>> from selkie.nlp.dep import Sentence, Word
   >>> s = Sentence()
   >>> s.append(Word(1, 'This', ('PRON', 'PRON'), 'this', '', 2, 'subj'))
   >>> s.append(Word(2, 'is', ('VB', 'VB'), 'be', '', 0, 'mv'))
   >>> s.append(Word(3, 'a', ('DT', 'DT'), 'a', '', 4, 'det'))
   >>> s.append(Word(4, 'test', ('N', 'N'), 'test', '', 2, 'prednom'))

The numbers must be sequential from 1; they provide a quality check.

Dependency files
................

On disk, the training and test files are in CoNLL dependency format.
The sents() method uses selkie.nlp.dep.conll_sents() to read them::

   >>> from selkie.nlp.dep import conll_sents
   >>> f = conll_sents(ds.train)
   >>> s = next(f)
   >>> len(s)
   14

The file 'depsent1' provides an example of the file
format::

   1       This    this    pron    pron    _       2       subj    2       subj
   2       is      is      vb      vb      _       0       mv      0       mv
   3       a       a       dt      dt      _       4       det     4       det
   4       test    test    n       n       _       2       prednom 2       prednom

Each sentence is (obligatorily) terminated by an empty line.  Fields
are separated by single tab characters.  There are ten fields:
*id, form, lemma, cpos, fpos, morph, govr, role, pgovr, prole.*

Universal Pos Tags
..................

The 'umap' versions of the treebanks are mapped from the 'orig'
versions using the tag tables of Petrov, Das &amp; McDonald [3300].
They are instances of UMappedDataset, which uses
UMappedDepFile::

   >>> ds = dep.dataset('dan.umap')
   >>> s = next(ds.sents('train'))
   >>> s[1].form
   'Samme'
   >>> s[1].cat
   'ADJ'

BioNLP
------

The BioNLP dataset contains biomedical texts with annotations.
