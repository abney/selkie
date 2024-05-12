
Parser
******

The dependency parser described here is based on Nivre (2007).  See
detailed discussion in [p138].

Example
-------

The parser starts by creating a **configuration** from the input
sentence::

   >>> from selkie.nlp.dp.parser import Configuration
   >>> c0 = Configuration(['the', 'dog', 'in', 'the', 'park', 'chased', 'the', 'cat'])
   >>> print(c0)
   Configuration:
       govr:                           
       role:                           
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *  |-

The sentence is displayed in the "form" row, and the (original) word
positions are in the row labeled "i."  A root pseudo-word "*root*" has
been added at the beginning of the original sentence.  The "\|-" marks the beginning of
the unprocessed input, and the "*" marks elements that are on the
stack.  Initially the stack contains only the root pseudo-word.
The information represented graphically by "*" and "\|-" is repeated
numerically next to the labels "stack" and "pointer."  Since "stack"
and "pointer" are redundant, I omit them going forward, in order to
save space.

There are four parser actions, the first of which is **shift,**
which moves one word from the input onto the stack::

   >>> c1 = c0.shift()
   >>> print(c1)
   Configuration:
       govr:                           
       role:                           
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *  *  |-            

Attachments are only possible between the word *S* on top of the stack and
the word *I* at the input pointer.  Attaching *S* as
dependent of *I* is **rightward** attachment, and
attaching *I* as dependent of *S* is **leftward** attachment.
In this case, we want rightward attachment to make "the" a dependent of "dog"::

   >>> c2 = c1.attach_right('spec')
   >>> print(c2)
   Configuration:
       govr:    2                      
       role:    sp                     
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *     |-                  

Once a word has been attached to the right, it is no longer eligible
as governor for later words, and so it is popped from the stack.  As
part of the attachment action, "the" has received a governor
(represented by word index) and role.

We shift again::

   >>> c3 = c2.shift()
   >>> print(c3)
   Configuration:
       govr:    2                      
       role:    sp                     
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *     *  |-               

Now the correct action is to attach "in" leftward as a modifier of
"dog"::

   >>> c4 = c3.attach_left('mod')
   >>> print(c4)
   Configuration:
       govr:    2     2                
       role:    sp    mo               
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *     *  *  |-            

As part of the attachment, "in" has been shifted from the input onto
the stack.  Because its governor is to the left, it is still eligible
to be a governor for later words.

The second "the" is at the input pointer; it should be attached to the
right::

   >>> c5 = c4.shift().attach_right('spec')
   >>> print(c5)
   Configuration:
       govr:    2     2  5             
       role:    sp    mo sp            
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *     *  *     |-         

Next attach "park" as object of "in"::

   >>> c6 = c5.attach_left('pobj')
   >>> print(c6)
   Configuration:
       govr:    2     2  5  3          
       role:    sp    mo sp po         
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *     *  *     *  |-

The word "park" has all its dependents.  Sooner or later, the parser
will pop it from the stack using the final action, **reduce**::

   >>> c7 = c6.reduce()
   >>> print(c7)
   Configuration:
       govr:    2     2  5  3          
       role:    sp    mo sp po         
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *     *  *        |- 

"In" is also complete; we may pop it and then attach "dog" as subject
of "chased"::

   >>> c8 = c7.reduce().attach_right('subj')
   >>> print(c8)
   Configuration:
       govr:    2  6  2  5  3          
       role:    sp su mo sp po         
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *                 |-

At this point, the parser may recognize that "chased" is the main
verb, and attach it to the root pseudo-word::

   >>> c9 = c8.attach_left('root')
   >>> print(c9)
   Configuration:
       govr:    2  6  2  5  3  0       
       role:    sp su mo sp po ro      
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *                 *  |-

To finish off the parse, we should shift, attach "the" rightwards to
"cat," and attach "cat" leftwards to "chased"::

   >>> c10 = c9.shift().attach_right('spec').attach_left('obj')
   >>> print(c10)
   Configuration:
       govr:    2  6  2  5  3  0  8  6 
       role:    sp su mo sp po ro sp ob
       form: *r th do in th pa ch th ca
       i:    0  1  2  3  4  5  6  7  8 
             *                 *     * 

Two reductions will clean up the stack and leave the parser in a final
state.


Reference
---------

Configurations
..............

A Configuration contains a stack and an input pointer.
One initializes a configuration either from a tokenized sentence (i.e., a
simple list of strings) or from a selkie.dep.Sentence instance, in
which case the words() method is called to get a list of strings.
The stack is initialized to contain just a root node.

The attribute words contains the sentence as list of strings,
with the pseudo-word '*root*' as the 0-th word.  The attribute
sent contains the Sentence (if any)::

   >>> c0 = Configuration(['this', 'is', 'a', 'test'])
   >>> c0.words
   ['*root*', 'this', 'is', 'a', 'test']
   >>> c0.sent
   >>>

The member pointer indicates the earliest word that is yet to be
processed.  Its value is initially 1::

   >>> c0.pointer
   1

The method input() indexes words relative to the pointer.  The
word at the pointer is number 0.  The return value is a word index,
or None if the given index is invalid::

   >>> c0.input(0)
   1
   >>> c0.input(-1)
   >>> c0.input(4)
   >>>

The stack contains word indices.  It is contained in the member
_stack, but it is accessed through the method
stack().  The bottom
of the stack is conceptually to the left (earlier words) and the top
is to the right (later words).  The top of the stack is position 0.
Invalid positions are defined to contain None::

   >>> c0.stack(0)
   0
   >>> c0.stack(1)
   >>>

The first few parsing actions are typically to shift words onto the
stack, with the result that the stack simply contains the first few
nonnegative integers.  But after some attachments are performed, the
stack will no longer have such a simple relationship to the sentence.
For example:::

   >>> c1 = c0.shift()
   >>> c2 = c1.attach_right('subj')
   >>> tmp = c2.shift()
   >>> tmp._stack
   [0, 2]

There is one more data structure, in the member _nodes.
It contains attachment information resulting from parsing actions.
There are four actions: shifting a word from the input onto the stack,
attaching the next input word leftwards (to the word on top of the
stack), attaching the top word on the stack rightwards (to the first
input word), and popping the stack.

The member _nodes contains one Node for each
word in the sentence (with 0 being the root node).  A Node has
the following members:

 * index — its position in the sentence, with the root at 0.

 * govr — the index of its governor.

 * role — its role with respect to its governor.

 * lc — the index of its leftmost left child.

 * rc — the index of its rightmost right child.

 * ls — the index of its preceding sibling, if it is a right child.

 * rs — the index of its following sibling, if it is a left child.

All except index may have the value None.

Elementary features
...................

The following methods are used to compute feature values.  They all
take a word index *w* as input, and they are forgiving in the sense
that they simply return None if *w* is None, or if the
requested feature does not exist.  The return values are either
strings or word indices, or None.

 * word(*w*) — the word form (string).

 * lemma(*w*) — the lemma (string).

 * cpos(*w*) — the coarse part of speech.  If the input is a CoNLL
   sentence, this is cat[0], and otherwise it is cat.

 * fpos(*w*) — the fine part of speech.  If the input is a CoNLL
   sentence, this is cat[1], and otherwise it is cat.

 * morph(*w*) — the morphological information (string).

 * true_govr(*w*) — the governor recorded in the
   original Sentence.  Signals an error if the configuration was
   not initialized from a Sentence.

 * true_role(*w*) — the role recorded in the original
   Sentence.

 * govr(*w*) — the governor, if the word has been attached.

 * role(*w*) — the role, if the word has been attached.

 * lc(*w*) — the leftmost child, if this word has any left children.

 * rc(*w*) — the rightmost child, if this word has any right children.

 * ls(*w*) — the left sibling, if this node is a right child and
   there are preceding right children.

 * rs(*w*) — the right sibling, if this node is a left child and
   there are any following left children.

 * is_complete(*w*)
   — indicates whether a given word has acquired all of its true
   dependents.  To be precise, it returns False if any of the
   unattached words in lookahead have the given word as true governor.

Continuing with our previous example:::

   >>> c2.word(0)
   '*root*'
   >>> c2.word(None)
   >>>
   >>> c2.govr(1)
   2
   >>> c2.role(1)
   'subj'
   >>> c2.lc(2)
   1

To illustrate the "supervised" methods, let us create a
configuration from a CoNLL sentence::

   >>> from selkie.core.io import ex
   >>> from selkie.nlp.dep import conll_sents
   >>> sent = next(conll_sents(ex.depsent2))
   >>> print(sent)
   0 *root* _   _     _ _
   1 a      pos a/pos A 2   
   2 b      pos b/pos B 4   
   3 c      pos c/pos C 2   
   4 d      pos d/pos D 0   
   5 e      pos e/pos E 7   
   6 f      pos f/pos F 3   
   7 g      pos g/pos G 0   
   8 h      pos h/pos H 7   
   >>> cc = Configuration(sent)

We shift the first word onto the stack and attach it rightwards,
leaving just the root on the stack and "b" as the next word of input:::

   >>> cc = cc.shift()
   >>> cc = cc.attach_right('A')
   >>> print(cc)
   Configuration 0.2:
       tgovr:    2  4  2  0  7  3  0  7 
       trole:    A  B  C  D  E  F  G  H 
       govr:     2                      
       role:     A                      
       cpos:  2  po po po po po po po po
       fpos:  2  po po po po po po po po
       form:  *r a  b  c  d  e  f  g  h 
       i:     0  1  2  3  4  5  6  7  8 
              *     |-                  

Now attach word 2 to the root (leftwards):::

   >>> cc = cc.attach_left('B')
   >>> print(cc)
   Configuration 0.3:
       tgovr:    2  4  2  0  7  3  0  7 
       trole:    A  B  C  D  E  F  G  H 
       govr:     2  0                   
       role:     A  B                   
       cpos:  2  po po po po po po po po
       fpos:  2  po po po po po po po po
       form:  *r a  b  c  d  e  f  g  h 
       i:     0  1  2  3  4  5  6  7  8 
              *     *  |-               

Now word 2 has a governor (albeit the incorrect one), but it is still
incomplete because word 3's true governor is 2:::

   >>> cc.govr(2)
   0
   >>> cc.true_govr(2)
   4
   >>> cc.true_govr(3)
   2
   >>> cc.is_complete(2)
   False

Attaching word 3 to word 2 completes word 2:::

   >>> cc = cc.attach_left('C')
   >>> print(cc)
   Configuration 0.4:
       tgovr:    2  4  2  0  7  3  0  7 
       trole:    A  B  C  D  E  F  G  H 
       govr:     2  0  2                
       role:     A  B  C                
       cpos:  2  po po po po po po po po
       fpos:  2  po po po po po po po po
       form:  *r a  b  c  d  e  f  g  h 
       i:     0  1  2  3  4  5  6  7  8 
              *     *  *  |-            
   >>> cc.is_complete(2)
   True

Actions
.......

The actions for an arc-eager stack-based parser are implemented.
As briefly mentioned above, there are four actions.

 * Shift — pushes the first input word onto the stack and
   moves the input pointer one position to the right.

 * Attach right — attaches the word on top of the stack
   rightwards, to the first input word.  The attached word is popped off
   the stack.  An error is signalled if the word on top of the stack already has
   a governor.

 * Attach left — attaches the first word in the input
   leftwards, to the word on top of the stack.  An error is signalled
   if the word to be attached already has a governor.
   The newly attached word
   is shifted onto the stack, and the input pointer is advanced.

 * Reduce — pops the stack.  It is assumed that the word on top
   of the stack has a governor, but no check is done.

Executing an action
...................

The configuration can be applied as a function to an abbreviated
action name: 'al' (attach left), 'ar' (attach right),
'sh' (shift), 're' (reduce).
An optional second argument provides the label, for the attachment
actions::

   >>> print(c2('al', 'mv'))
   Configuration:
       govr:    2  0       
       role:    su mv      
       form: *r th is a  te
       i:    0  1  2  3  4 
             *     *  |-   

Supervised oracle
.................

An oracle function takes a configuration and returns the
next action to take.
The function supervised_oracle() expects a configuration
constructed from a labeled sentence, and looks at the true stemma to
determine the next action.
The configuration must have a value for conll::

   >>> s = next(conll_sents(ex.depsent1))
   >>> print(s)
   0 *root* _    _    _       _
   1 This   pron this subj    2   
   2 is     vb   be   mv      0   
   3 a      dt   a    det     4   
   4 test   n    test prednom 2   

Here is an example of using the supervised oracle:::

   >>> c = Configuration(s)
   >>> from selkie.nlp.dp.parser import supervised_oracle
   >>> supervised_oracle(c)
   ('sh', None)
   >>> (act, role) = _
   >>> c = c(act, role)
   >>> print(c.buffer_string())
   *r Th | is a te

The oracle works as follows.  Let *L* and *R* be the two words on
either side of the pointer.

 * If *R* doesn't exist, stop.

 * If *R*'s true governor is *L*, and *R* is unattached, then attach-left.

 * If *L*'s true governor is *R*, and *L* is unattached, then attach-right.

 * If *L* is attached and complete (i.e., no word in the lookahead
   is governed by *L*), then reduce.

 * Otherwise, shift.

One can perform an entire computation using the function
computation().  The output is a list of triples
(*config, act, role*)::

   >>> from selkie.nlp.dp.parser import computation
   >>> comp = computation(s, supervised_oracle)
   >>> (cfg, act, role) = comp[2]
   >>> print(cfg)
   Configuration 0.2:
       tgovr:    2  0  4  2 
       trole:    su mv de pr
       govr:     2          
       role:     su         
       cpos:  2  pr vb dt n 
       fpos:  2  pr vb dt n 
       form:  *r Th is a  te
       i:     0  1  2  3  4 
              *     |-      

For convenience, there is also a print_computation() function:::

   >>> from selkie.nlp.dp.parser import print_computation
   >>> print_computation(comp)
   *r | Th is a te
    -> sh None
   *r Th | is a te
    -> ar subj
   *r | is a te
    -> al mv
   *r is | a te
    -> sh None
   *r is a | te
    -> ar det
   *r is | te
    -> al prednom
   *r is te |
    -> stop None

Creating a classifier training set
..................................

The function instances() takes a Sentence and a
feature function, and produces a sequence of machine-learning
instances.  It calls computation() to get a sequence of
configurations with actions.  Each step produces a machine-learning instance.
The action is the instance label (the role, if any, is appended to the
action), and the instance's features are the result of applying the
feature function to the configuration::

   >>> from selkie.nlp.dp.parser import instances, simple_features
   >>> for inst in instances(s, simple_features):
   ...     print(inst)
   ...
   sh s2:None s1:*root* la1:This la2:is
   ar_subj s2:*root* s1:This la1:is la2:a
   al_mv s2:None s1:*root* la1:is la2:a
   sh s2:*root* s1:is la1:a la2:test
   ar_det s2:is s1:a la1:test la2:None
   al_prednom s2:*root* s1:is la1:test la2:None

The feature function receives a configuration as input and returns a
list of attribute-values pairs.  Simple_features() is a fairly
trivial example::

   >>> (c,_,_) = comp[2]
   >>> print(c)
   Configuration 0.2:
       tgovr:    2  0  4  2 
       trole:    su mv de pr
       govr:     2          
       role:     su         
       cpos:  2  pr vb dt n 
       fpos:  2  pr vb dt n 
       form:  *r Th is a  te
       i:     0  1  2  3  4 
              *     |-      
   >>> simple_features(c)
   [('s2', None), ('s1', '*root*'), ('la1', 'is'), ('la2', 'a')]

Features
--------

The module selkie.nlp.dp.features contains a feature compiler,
which takes a complex feature specification and constructs a function
from it.  The function takes a computation as input and returns a
feature vector (instance) as output.

Compile
.......

The main function is compile(), which takes a set of feature
specifications (a string) and produces a function that maps
configurations to instances::

   >>> from selkie.nlp.dp.features import *
   >>> cfgs = [cfg for (cfg,_,_) in comp]
   >>> f = compile('fpos stack 0, fpos input 0')
   >>> f(cfgs[0])
   [('fpos.input.0', 'pron')]
   >>> f(cfgs[1])
   [('fpos.stack.0', 'pron'), ('fpos.input.0', 'vb')]

By default, features with a null value are suppressed.  One can change
this behavior by passing nulls=True to compile()::

   >>> f = compile('fpos stack 0, fpos input 0', nulls=True)
   >>> f(cfgs[0])
   [('fpos.stack.0', 'null'), ('fpos.input.0', 'pron')]

Format
......

Feature specifications are built up from accessor functions such as
fpos and stack.  The simplest specifications are of the
form 'stack 0' or 'input 2', in which the argument is a
number.  Only the functions stack and input may be used in
this way.  All other functions take a subexpression as argument.
The available functions are::

 * form,
 * lemma,
 * cpos,
 * fpos,
 * morph,
 * govr,
 * role,
 * lc,
 * rc,
 * ls,
 * rs.

Multiple feature specifications may be separated either by comma or
newline.


Load
....

One can alternatively load feature specifications from a file.

Implementation
..............

The function load() simply calls compile() on the contents
of the file.  The function compile() first splits the input text
into feature specs.  Feature specs may be separated either by commas
or newlines::

   >>> from selkie.nlp.dp.features import specs
   >>> sps = specs('form input 0, fpos input 0, role lc input 0')
   >>> sps
   ['form input 0', 'fpos input 0', 'role lc input 0']

The specs are then used to create a FunctionList object, which
in turn uses _compile1() to turn each spec into a
function.

The function _compile1() takes a spec consisting of a
sequence of words, like ['role', 'lc', 'input', '0'].  The first
word is the *operator.*  The operators stack and input
are nonrecursive; they take the next word (which must be the last
word) as argument.  For example,::

   _compile1(['input', '0'])

converts the '0' to an int and returns the function:::

   lambda cfg: cfg.input(0)

The other operators are recursive.  For example, if the first word is lc, the
remainder of the spec is passed to _compile1() to
obtain a function f, and the return value is:::

   lambda cfg: cfg.lc(f(cfg))

The result is always a function that takes a configuration as input
and returns a string or None.


Trees
-----

The module selkie.nlp.dp.tree provides the
class DepTree, but it is not actually used and is likely to
go away.

Evaluation
----------

evaluate
........

This is the main function.  It takes a parser, a list of sentences
with gold pgovrs and proles, and prints out evaluation information.
The parser should place its output in the govr and role slots, not
pgovr and prole.  One may specify excludepunc=False to count
punctuation tokens.  (They are ignored by default.)  One may provide
output=*stream* to specify
an output stream other than stdout::

   >>> from selkie.nlp.dp.eval import evaluate
   >>> evaluate(parser, sents)

ispunc
......

The function ispunc() returns True if all the characters
in the given string have a Unicode category beginning with "P"::

   >>> from selkie.nlp.dp.eval import ispunc
   >>> ispunc('.')
   True
   >>> ispunc('Dr.')
   False

eval_sent
.........

The function eval_sent() evaluates a single sentence.  Its
arguments are *pred* and *truth.*  It considers the govrs
and roles of the predicted sentence, but the pgovrs and proles of the
true sentence.  (A projective dependency parser can produce
non-projective output if it ever fails to attach a word, so the output
of even a projective dependency parser is stored in the govr/role
slots rather than the pgovr/prole slots.)

The outputs are *las, uas, la, n,* where *las* is the
number of words that have the correct govr and role, *uas* is
the number of words that have the correct govr, *la* is the
number of words that have the correct role, and *n* is the
number of words.  Nota bene: these are counts, not proportions.
Note also that *n* will be less than the length of the
sentence.  The length of the sentence includes the root token
(position 0), which is never included in *n.*
Also, by default, punctuation tokens are ignored.
(One can cause them to be counted by specifying excludepunc=False.)
::

   >>> from selkie.nlp.dp.eval import eval_sent
   >>> pred = next(conll_sents(ex.depsent3_pred))
   >>> gold = next(conll_sents(ex.depsent3_gold))
   >>> eval_sent(pred, gold)
   (2, 3, 2, 4)
   >>> eval_sent(pred, gold, excludepunc=False)
   (3, 4, 3, 5)

compare
.......

The function compare() prints out a detailed comparison of a
predicted and a gold sentence::

   >>> from selkie.nlp.dp.eval import compare
   >>> compare(pred, gold)
   1   This G R 2 subj 2 subj   
   2   is   G R 0 mv   0 mv     
   3   a        2 pt   4 det    
   4   test G   2 obj  2 prednom
   5 * .        2 obj  2 prednom
   
   LAS: 2 4 0.5 
   UAS: 3 4 0.75
   LA:  2 4 0.5

Punctuation tokens are marked with "*" in the second column.
Tokens marked "G" contribute to the UAS score, tokens marked
"R" contribute to the LA score, and tokens marked
"G R" contribute to the LAS score.
