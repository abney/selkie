##  @package seal.nlp.bot
#   A chatbot.

import sys
from traceback import print_exception

from .data import ex
from .interp import Interpreter
from .logic import KB, Prover, clausify

default_grammar = ex('sg2a')

#--  Event  --------------------------------------------------------------------

##  An event in the simulator.

class Event (object):

    ##  Constructor.

    def __init__ (self, agent, action):
        ##  The agent performing the action.
        self.agent = agent
        ##  The action.
        self.action = action

    ##  String representation.

    def __str__ (self):
        return self.agent.name + ' ' + ' '.join(self.action)


#--  Player  -------------------------------------------------------------------

##  A player.

class Player (object):

    ##  Constructor.

    def __init__ (self, engine):
        ##  The player's name.
        self.name = 'Player'
        ##  Pointer to the game engine.
        self.engine = engine

    ##  Call the player on a percept.  Display it to the user and get their
    #   response.

    def __call__ (self, percept):
        if percept: print(percept)
        while True:
            line = self.input()
            if not line:
                sys.stdout.write('\nBye\n')
                sys.stdout.flush()
                return ('quit',)
            line = line.rstrip('\r\n')
            if len(line) == 0:
                continue
            elif line[0] == ':':
                self.command(line[1:].split())
            else:
                return ('say', line)

    ##  Accept a line of input.

    def input (self):
        sys.stdout.write('> ')
        sys.stdout.flush()
        return sys.stdin.readline()

    ##  Execute a command.
    #    - 'help' - Print a help message.
    #    - '?' - Synonym for 'help'.
    #    - 'clause' - Print out the clauses for the last input.
    #    - 'clauses' - Synonym for 'clause'.
    #    - 'kb' - Print out the KB.
    #    - 'forget' - Forget a clause.  Argument may be clause number,
    #      or 'that' for the most recent one, or 'all' to clear the KB.
    #    - 'parse' - Show the parse for the previous input.
    #    - 'chart' - Show the chart for the previous input.
    #    - 'reload' - Reload the grammar and other data files.
    #    - 'err' - Print out the last error.
    #    - 'trace' - Toggle tracing on or off.

    def command (self, com):
        npc = self.engine.npc

        if com[0] in ('help', '?'):
            print(':? - this help message')
            print(':help - this help message')
            print(':clauses - show the clauses from the prev sent')
            print(':kb - show the knowledge base')
            print(':forget that - delete the last clause from the kb')
            print(':forget all - clear the kb')
            print(':forget <i> - delete the i-th clause from the kb')
            print(':parse - show the parse & interp of the prev sent')
            print(':chart - rerun the parser with tracing on')
            print(':reload - reload .g, .lex, .defs')
            print(':err - print the previous error')
            print(':trace - toggle tracing')

        elif com[0] in ('clause', 'clauses'):
            expr = npc.previous_expr
            print('expr=', expr)
            clauses = clausify(expr, trace=True)
            for clause in clauses:
                print(clause)

        elif com[0] == 'kb':
            print(npc.kb)

        elif com[0] == 'forget':
            if com[1] == 'that':
                del npc.kb[-1]
            elif com[1] == 'all':
                npc.kb.clear()
            else:
                id = int(com[1])
                npc.kb.delete(id)

        elif com[0] == 'parse':
            sent = npc.previous_sent
            print('sent=', repr(sent))
            npc.interpreter(sent, trace=True)

        elif com[0] == 'chart':
            sent = npc.previous_sent
            print('sent=', repr(sent))
            npc.interpreter.parser(sent, trace=True)

        elif com[0] == 'reload':
            npc.interpreter.reload()

        elif com[0] == 'err':
            e = npc.exception
            if e:
                print_exception(*e)

        elif com[0] == 'trace':
            npc.trace = not npc.trace

        else:
            print('Unrecognized command')


##  A "pre-programmed" player for test purposes.

class BatchPlayer (Player):

    ##  Constructor.  The source should be an iterable containing strings
    #   simulating lines that the user types in.  (Do not include terminating
    #   newlines.)

    def __init__ (self, engine, source):
        Player.__init__(self, engine)

        ##  An iteration over strings.
        self.source = iter(source)

    ##  Pretend that the user types in the next line of input.  It is echoed
    #   and returned to the caller.

    def input (self):
        try:
            line = next(self.source)
            sys.stdout.write('> ')
            sys.stdout.write(line)
            sys.stdout.write('\n')
            return line
        except StopIteration:
            return None


#--  NPC  ----------------------------------------------------------------------

##  The non-player character, which is to say, the conversational agent.

class NPC (object):

    ##  Constructor.

    def __init__ (self, grammar):

        ##  Its name.
        self.name = 'NPC'

        ##  An Interpreter.
        self.interpreter = Interpreter(grammar)

        ##  A KB.
        self.kb = KB()

        ##  A Prover.
        self.prover = Prover(self.kb)

        ##  Tracing flag.
        self.trace = False

        ##  The previous sentence.
        self.previous_sent = None

        ##  The semantic translation of the previous sentence.
        self.previous_expr = None

        ##  The most recent exception.
        self.exception = None

        ##  The most recent traceback.
        self.traceback = None

    ##  Call the agent on a percept.  The main agent code.

    def __call__ (self, percept):
        if self.trace: print('#NPC: percept=', repr(percept))
        if percept and percept.action[0] == 'say':
            try:
                sent = percept.action[1]
                self.previous_sent = sent
                exprs = self.interpreter(sent, trace=self.trace)
                if not exprs:
                    return ('say', "I don't understand")
                expr = exprs[0]
                self.previous_expr = expr
                act = speech_act(expr)
                if act == 'inform':
                    if self.trace: print('#Add to KB:', expr)
                    self.kb.add(expr)
                    return ('say', 'OK')
                elif act == 'ask':
                    if self.trace: print('#Query:', expr)
                    answers = self.prover(expr)
                    if answers:
                        return ('say', ', '.join(answers))
                    else:
                        return ('say', "I don't know")
                elif act == 'greet':
                    if self.trace: print('#Greet:', expr)
                    return ('say', 'hello')
            except Exception:
                self.exception = sys.exc_info()
                if self.trace:
                    print('#NPC: Caught an exception')
                    print_exception(*self.exception)
                return ('say', 'Ugh, my brain hurts')


#--  Pragmatics (such as it is)  -----------------------------------------------

##  Returns a speech action: one of 'ask', 'greeting', 'inform'.

def speech_act (expr):
    if expr[0] in ('wh', 'yn'):
        return 'ask'
    elif expr[0] == 'greeting':
        return 'greet'
    else:
        return 'inform'


#--  Engine  -------------------------------------------------------------------

##  The game engine.

class Engine (object):

    ##  Constructor.

    def __init__ (self, grammar=default_grammar, input=None):
        if input is None: player = Player(self)
        else: player = BatchPlayer(self, input)

        ##  The non-player character.
        self.npc = NPC(grammar)
        ##  The player (user).
        self.player = player
        ##  All agents.
        self.agents = [self.player, self.npc]

    ##  Returns the Grammar.
    def grammar (self): return self.npc.interpreter.parser.grammar

    ##  Returns the Parser.
    def parser (self): return self.npc.interpreter.parser

    ##  Returns the Interpreter.
    def interpreter (self): return self.npc.interpreter

    ##  Returns the KB.
    def kb (self): return self.npc.kb

    ##  Returns the Prover.
    def prover (self): return self.npc.prover

    ##  Run.

    def run (self):
        i = 0
        percept = Event(self.npc, ('enter',))
        while True:
            agent = self.agents[i]
            i += 1
            if i >= len(self.agents): i = 0
            action = agent(percept)
            if action:
                if action[0] == 'quit': break
                percept = Event(agent, action)
            else:
                percept = None


#--  Run  ----------------------------------------------------------------------

##  Create an Engine and run it.

def run (grammar=default_grammar):
    Engine(grammar).run()

if __name__ == '__main__':
    run()
