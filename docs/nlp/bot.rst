
``selkie.bot`` — Conversational agent
=====================================

Using the engine
----------------

The previous pages have described the various components of a
conversational agent: parser, semantic
interpreter, and resolution theorem prover.  The ``selkie.bot`` module
encapsulates them in a conversational agent, represented by the class
``NPC`` (non-player character), and embeds the agent in a bare-bones
environment, in the style of an interactive fiction engine.

Here is an example of an interaction, with commentary::

   $ python -m selkie.bot
   NPC enter
   > 

The engine does provide an environment for multiple characters and
event types, but it is a stub.  There are two characters: Player
and Non-Player Character (NPC).  The only event type with any
non-trivial implementation is "say."  Anything typed at the prompt
is converted to a "say" action whose agent is Player::

   > all humans are mortal
   NPC say OK
   > Socrates is human
   NPC say OK
   > who is mortal
   NPC say Socrates
   > is Socrates mortal
   NPC say yes
   > is Socrates human
   NPC say yes
   > is Zeus human
   NPC say I don't know
   > Zeus is not mortal
   NPC say OK
   > is Zeus human
   NPC say no

Several debugging commands are available to examine the internal state
of the conversational agent::

   > :kb
   1. -(human _2) +(mortal _2)
   2. +(human Socrates)
   27. -(mortal Zeus)

The KB contains three clauses.  "``_2``" is an anonymous
variable; variables are interpreted as universally bound.  A clause
consists of literals, which have a polarity (positive or negated), and
are implicitly connected by disjunction.  Clauses are connected by
conjunction.

For example, clause 1 states that either ``_2`` is not human, or
``_2`` is mortal.  That is equivalent to "if *x* is human, then
*x* is mortal."  Clause 2 states that Socrates is human, and clause
27 states that Zeus is not mortal.  All three clauses are asserted to
be simultaneously true.

Here is another example (adapted from Russell &amp; Norvig, Chapter 9),
illustrating case-based reasoning of the sort that a purely backward
chaining reasoner does not support::

   > either Smith killed Tuna or Curiosity killed Tuna
   NPC say OK
   > any one who loves animals does not kill animals
   NPC say OK
   > Tuna is a cat
   NPC say OK
   > every cat is an animal
   NPC say OK
   > Smith loves animals
   NPC say OK
   > does Smith love Tuna
   NPC say yes
   > did Smith kill Tuna
   NPC say I don't know

It would seem NPC *ought* to know.  The problem is that "any
one" is interpreted to mean "any *person,*" and NPC does not
know that Smith is a person::

   > Smith is a person
   NPC say OK
   > did Smith kill Tuna
   NPC say no
   > who killed Tuna
   NPC say Curiosity

At this point, the KB contains the following clauses::

   > :kb
   1. -(human _2) +(mortal _2)
   2. +(human Socrates)
   27. -(mortal Zeus)
   35. +(kill Smith Tuna) +(kill Curiosity Tuna)
   36. -(person _18) +(animal (_Sk1 _18)) -(animal _20) -(kill _18 _20)
   37. -(person _18) -(love _18 (_Sk1 _18)) -(animal _20) -(kill _18 _20)
   38. +(cat Tuna)
   39. -(cat _22) +(animal _22)
   40. -(animal _25) +(love Smith _25)
   63. +(person Smith)

Backward-chaining systems like Prolog permit only Horn clauses
(clauses containing exactly one positive literal).
Clauses 35 and 37 are not Horn clauses; the reasoning illustrated here
is not supported by Prolog.

Additional debugging commands allow one to examine the most important
intermediate representations.  The three main components are the
parser, the interpreter, and the reasoner.  The parser takes a
sentence and converts it to a parse tree.  The process can be seen
using the ``:chart`` command::

   > who does every cat love
   NPC say I don't know
   > :chart
   sent= 'who does every cat love'
   Add Node [0 WhPron.sg 1] who WhPron.sg : wh
   Add Edge (WhNP.$0 -> [0 WhPron.sg 1] * {sg})
   Add Node [0 WhNP.sg 1] (WhNP.$0 -> [0 WhPron.sg 1] * {sg})
   Add Edge (WhInv -> [0 WhNP.sg 1] * Aux.$0.$1 NP.$0 VP.$1.+ {* *})
   ...
   Add Edge (Start -> [0 Root 5] * {})
   Add Node [0 Start 5] (Start -> [0 Root 5] * {})
   Add Edge (VP.$0.- -> [4 V.base.t.0 5] * NP.* MP.$1 {base 0})
   Add Edge (VP.$0.+ -> [4 V.base.t.0 5] * MP.$1 {base 0})
   Add Edge (VP.$0.$1 -> [4 V.base.t.0 5] * NP.* SC.$2.$1 {base * 0})

The interpreter takes the parse tree and converts it to a
predicate-calculus expression.  This is accomplished in several steps,
which are shown by the ``:parse`` command::

   > :parse
   sent= 'who does every cat love'</p>
   <p>
   who does every cat love
   #Tree:
     Start : $1
       Root : (wh _9 (!g= _9 $1))
         WhInv : (!qs ($4 $3))
           WhNP.sg : $1
             WhPron.sg who : wh
           Aux.sg.base does : None
           NP.sg : (!q $1 _7 ($2 _7))
             Det.sg every : every
             N2.sg : $1
               N1.sg : $1
                 N.sg cat : cat
           VP.base.+ : (lambda _8 ($1 _8 !g))
             V.base.t.0 love : love
   #Raise quantifiers:
     Start : $1
       Root : (wh _9 (!g= _9 $1))
         NP.sg : ($1 _7 ($2 _7) $3)
           Det.sg every : every
           N2.sg : $1
             N1.sg : $1
               N.sg cat : cat
           WhInv : ($4 $3)
             WhNP.sg : $1
               WhPron.sg who : wh
             Aux.sg.base does : None
             NP.sg : _7
             VP.base.+ : (lambda _8 ($1 _8 !g))
               V.base.t.0 love : love
   #Translation:
     (wh _9 (!g= _9 (every _7 (cat _7) ((lambda _8 (love _8 !g)) _7))))
   #Replace gaps:
     (wh _9 (every _7 (cat _7) ((lambda _8 (love _8 _9)) _7)))
   #Definitions:
     (wh _9 (forall _7 (if (cat _7) ((lambda _8 (love _8 _9)) _7))))
   #Lambda reduction:
     (wh _9 (forall _7 (if (cat _7) (love _7 _9))))

Finally, the reasoner converts predicate calculus expressions to
clauses, before doing inference proper.  The steps in the conversion
can be seen by invoking the ``:clause`` command::

   > :clause
   expr= (wh _3 (forall _1 (if (cat _1) (love _1 _3))))
   #Standardize variables:
     (wh _13 (forall _14 (if (cat _14) (love _14 _13))))
   #Expand query:
     (forall _13 (if (forall _14 (if (cat _14) (love _14 _13))) (_Ans _13)))
   #Eliminate implications:
     (forall _13 (or (not (forall _14 (or (not (cat _14)) (love _14 _13)))) (_Ans _13)))
   #Lower negation:
     (forall _13 (or (exists _14 (and (cat _14) (not (love _14 _13)))) (_Ans _13)))
   #Skolemize:
     (or (and (cat (_Sk2 _13)) (not (love (_Sk2 _13) _13))) (_Ans _13))
   #Conjunctive normal form:
     [[(cat (_Sk2 _13)), (_Ans _13)], [(not (love (_Sk2 _13) _13)), (_Ans _13)]]
   #Clauses:
     4. +(cat (_Sk2 _13)) ; +(_Ans _13)
     5. -(love (_Sk2 _13) _13) ; +(_Ans _13)
   4. +(cat (_Sk2 _13)) ; +(_Ans _13)
   5. -(love (_Sk2 _13) _13) ; +(_Ans _13)

The parser and interpreter are controlled by a grammar, a lexicon, and
a set of defined symbols.  To give a sense of the contents, I give the
first few lines of each section of the current default grammar,
``sg2a.g``.  The rewrite rules::

   Start -> Root : $1
   Start -> NP.* : $1
   Start -> PP.* : $1
   Start -> Greeting : ($1)
   
   # Clauses
   Root -> S.-               : $1
   Root -> YN                : (yn $1)
   Root -> WhInv             : (wh @ (!g= @ $1))
   Root -> Wh                : (wh @ (!g= @ $1))

Each line is a grammar rule, which consists of a syntactic portion and
a semantic attachment, separated by a colon.  The format is discussed
in more detail below.

The first few lines of the lexicon section are as follows::

   a        Det.sg : some
   a        IndefArt
   all      Det.pl   : every
   am       Aux.1s.pred
   am       Aux.1s.ing
   am       Aux.1s.enp

The generalized quantifiers ``some`` and ``every`` are defined in
terms of the basic quantifiers ``forall`` and ``exists`` in the
macros section::

   every x R S: (forall x (if R S))
   some x R S: (exists x (and R S))
   nsome x R S: (not (exists x (and R S)))

Agents, events, engine
----------------------

In our model, an **agent** is essentially a function that takes a
percept and returns an action.  A percept is an **event**, which is
the combination of an agent and an action.  An **action** is a tuple
whose first element is a string representing the action type, and
whose remaining elements are determined by the type.  Currently, the
primary action type is ``'say'``; it takes a single argument, which
is a string representing the utterance.  Two other action types
occur.  The system generates an ``'enter'`` action when the game
begins, and the user generates a ``'quit'`` action by hitting
control-D.

.. py:class:: Event(agent, action)

   The class ``Event`` represents an event.  It is created from an
   agent and action:
   
   >>> from selkie.bot import Engine, Event
   >>> eng = Engine()
   >>> p = eng.player
   >>> e = Event(p, ('say', 'hi'))
   >>> e.agent == p
   True
   >>> e.action
   ('say', 'hi')

.. py:class:: NPC(g)

   The conversational agent is an instance of the class ``NPC``
   ("non-player character").  It requires a grammar:
   
   >>> from selkie.bot import NPC
   >>> from selkie.data import ex
   >>> npc = NPC(ex('sg2a'))

   It creates an interpreter (which contains a parser), a KB, and a
   prover.
   
   .. py:attribute:: interpreter

      A selkie.interp.Interpreter instance.

   .. py:attribute:: kb

      A selkie.logic.KB instance.

   .. py:attribute:: prover

      A selkie.logic.Prover instance.

   .. py:method:: __call__(percept)

      The ``__call__()`` method accepts a percept.  The NPC responds only
      if the type is ``'say'``.  Otherwise it returns ``None``.
      
      >>> npc(e)
      ('say', 'hello')
      >>> npc(Event(p, ('foo',)))
      >>> 
      
      In the case of a ``'say'`` event, the argument of the event is the
      utterance.  The NPC applies the interpreter
      to the utterance to get a list of expressions.
      If the sentence does not parse, the NPC responds "I don't
      understand."
      
      >>> npc(Event(None, ('say', 'sdfsdf')))
      ('say', "I don't understand")

      If there are multiple interpretations, the NPC simply takes the
      first.  Then it calls ``speech_act()`` on the expression to
      classify it as ``'ask'``, ``'greet'``, or ``'inform'``.
      
      >>> from selkie.expr import parse_expr
      >>> from selkie.bot import speech_act
      >>> speech_act(parse_expr('(greeting)'))
      'greet'
      >>> speech_act(parse_expr('(wh x (human x))'))
      'ask'
      >>> speech_act(parse_expr('(human Socrates)'))
      'inform'
      
      In response to a greeting, the NPC says "hello."  In response to a
      question, the NPC queries its KB and speaks the answer or answers.  If
      no answer is found, it says "I don't know."  Finally, in response to
      an inform, the NPC adds the expression to the KB and says "OK."
      If anything throws an exception, the NPC traps the exception and says
      "Ugh, my brain hurts."

.. py:class:: Player(engine)

   The class ``Player`` is an avatar of the user.  It is given access to the
   engine to allow the user to examine the internal state of the engine,
   including the internal state of the NPC, via
   the debugging commands described below.
   
   >>> from selkie.bot import Player
   >>> p = Player(eng)
   
   The player is an agent, meaning
   that it has a ``__call__()`` method that expects a percept and
   returns an action.  It simply prints the percept, and then prompts the
   user to "say" something::
   
      >>> p(Event(npc, ('say', 'hello')))
      NPC say hello
      > 
   
   Whatever the user types (a single line) is wrapped in a ``'say'``
   action and returned::
   
      >>> p(Event(npc, ('say', 'hello')))
      NPC say hello
      > hello
      ('say', 'hello')
   
   The user's input is "hello" (in boldface), and ``('say', 'hello')`` is
   the return value from the original call.
   
   If the user types a line beginning with a colon, it is interpreted as
   a debugging command.  Debugging commands produce some output, and then
   a new prompt is generated.  However, the call to the player does not
   return until an utterance - a line not beginning with colon - is
   typed::
   
      >>> p(Event(npc, ('enter',)))
      NPC enter
      > :help
      :? - this help message
      :help - this help message
      :clauses - show the clauses from the prev sent
      :kb - show the knowledge base
      :parse - show the parse & interp of the prev sent
      :reload - reload .g, .lex, .defs
      :err - print the previous error
      > :kb
      > the dog barked
      ('say', 'the dog barked')
   
   The debugging commands print out information about the internal state
   of the NPC: the parse tree and its interpretation, the mapping from
   expression to clauses, the KB, the identity of the error if an error
   was encountered.
   
   If the user presses control-D in response to the player prompt, the
   player returns the action ``(quit,)``.

.. py:class:: Engine

   The class ``Engine`` runs the simulation.  It creates an NPC and
   player, and an initial event, in which the NPC enters.  Then it enters
   a loop in which it alternates between agents.  It calls the current
   agent with the current event, and the combination of current agent and
   the action that it returns, constitutes the next event, which is
   passed to the other agent.  The loop continues until a ``'quit'``
   action is encountered.
