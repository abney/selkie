##  \package seal.nlp.gdev
#   Grammar development tool.

import os, traceback
from .data import path
from .io import Fn
from .grammar import Grammar
from .parser import Parser, Chart


#--  Parse  --------------------------------------------------------------------

##  A parse.

class Parse (object):

    ##  Constructor.

    def __init__ (self, sent):

        ##  The sentence.
        self.sent = sent

        ##  The parse trees.
        self.trees = None

        ##  The chart.
        self.chart = None

        dev = sent.dev
        p = dev.parser
        self.trees = p(sent.words, dev.trace_parse)
        if self.trees is None:
            self.chart = Chart(p)

    ##  Content detail, as a string.

    def __str__ (self):
        lines = []
        if self.trees:
            lines.append('#Parses: %d' % len(self.trees))
            for i,tree in enumerate(self.trees):
                lines.append('Parse %d:' % i)
                lines.append(str(tree))
        elif self.chart:
            lines.append('Chart:')
            lines.append(str(self.chart))
        return '\n'.join(lines)


#--  Sent  ---------------------------------------------------------------------

##  A sentence.

class Sent (object):

    ##  Constructor.

    def __init__ (self, dev, i, words, label=None):

        ##  The dev instance.
        self.dev = dev

        ##  Sentence index.
        self.i = i

        ##  The words.
        self.words = words

        ##  Sentence label.
        self.label = label

        ##  Trees.
        self.trees = None

        ##  Chart.
        self.chart = None

    ##  Summary line.

    def summary_line (self):
        p = Parse(self)
        n = len(p.trees or [])
        if (n == 0 and self.label == ' ') or (n > 0 and self.label == '*'):
            warn = '!'
        else:
            warn = ' '
        return '[%d] %s %d %s%s' % (self.i, warn, n, self.label, ' '.join(self.words))

    ##  String representation.

    def __repr__ (self):
        return '[%d] %s %s' % (self.i, self.label, ' '.join(self.words))


#--  Dev  ----------------------------------------------------------------------

##  It is a grammar directory if it is a directory containing a file 'main.g'.

def is_grammar_dir (fn):
    return os.path.isdir(fn) and os.path.exists(os.path.join(fn, 'main.g'))

##  The interactive tool.

class Dev (object):

    ##  Constructor.

    def __init__ (self):

        ##  The grammar path.
        self.path = ['.', path('examples'), path('eng')]

        self.__grammars = None

        ##  Prefix.
        self.prefix = None

        ##  Sentences.
        self.sents = None

        ##  The grammar.
        self.grammar = None

        ##  The parser.
        self.parser = None

        ##  Whether to trace parsing.
        self.trace_parse = False

        ##  Semantic model.
        self.model = None

        ##  Semantic assignment of values to variables.
        self.assignment = None

        ##  Current index.
        self.i = 0

        ##  Temporary sentence.
        self.tmpsent = None

    ##  Returns a dict mapping grammar names to filenames.
    #   The value is computed and cached the first time it is called.

    def grammars (self):
        if self.__grammars is None:
            self.__grammars = {}
            for dir in self.path:
                for fn in os.listdir(dir):
                    if fn.endswith('.g'):
                        name = fn[:-2]
                        if name not in self.__grammars:
                            self.__grammars[name] = Fn(os.path.join(dir, name))
                    elif is_grammar_dir(os.path.join(dir, fn)):
                        if fn not in self.__grammars:
                            self.__grammars[fn] = Fn(os.path.join(dir, fn))
        return self.__grammars

    ##  Print out the grammar names.

    def ls (self):
        gtab = self.grammars()
        for name in sorted(gtab):
            print(name)

    ##  Get the i-th sentence.

    def __getitem__ (self, i):
        return self.sents.__getitem__(i)

    ##  Reload the sentences and grammar.

    def reload (self):
        self.load_sents()
        self.load_grammar()
        #self.parse_all()

    ##  Load the sentences.

    def load_sents (self):
        fn = self.prefix.sents
        if not fn.exists(): return
        self.sents = []
        for n, line in enumerate(open(fn)):
            line = line.rstrip('\r\n')
            if (not line) or line.startswith('#'): continue
            label = line[0]
            sent = line[1:].split()
            if label not in [' ', '*']:
                raise Exception('%s line %d: bad label' % (fn, n+1))
            self.sents.append(Sent(self, n, sent, label))
        
    ##  Load the grammar.

    def load_grammar (self):
        fn = self.prefix.g
        self.grammar = Grammar(fn)
        self.parser = Parser(self.grammar)

    ##  Parse all sentences.

    def parse_all (self):
        for sent in self.sents:
            sent.parse()
        if self.tmpsent:
            self.tmpsent.parse()

    ##  Not implemented.

    def value (self, s):
        raise Exception('Unimplemented')
        # e = self.lp.parse(s)
        # return self.evaluate(e)

    ##  Print summary lines for all sentences.

    def print_sents (self):
        for sent in self.sents:
            print(sent.summary_line())

    ##  The contents in string form.

    def __str__ (self):
        lines = []
        for sent in self.sents:
            lines.append('')
            lines.append(repr(sent))
        return '\n'.join(lines)

    ##  Print the current sentence.

    def print_sent (self):
        if self.tmpsent: sent = self.tmpsent
        elif self.sents: sent = self.sents[self.i]
        else: return

        print()
        print(sent)
        print(Parse(sent))

    ##  Advance to the next sentence.

    def step_forward (self):
        self.tmpsent = None
        self.i += 1
        if self.i >= len(self.sents): self.i = 0

    ##  Go back one sentence.

    def step_back (self):
        self.tmpsent = None
        self.i -= 1
        if self.i < 0: self.i = len(self.sents) - 1

    ##  Jump to the i-th sentence.

    def goto (self, i):
        self.tmpsent = None
        if i < 0: i += len(self.sents)
        if i < 0 or i >= len(self.sents):
            raise KeyError('Sentence number out of bounds')
        self.i = i

    ##  Whether an input string looks like a valid sentence.  "Valid" means
    #   pure-alphabetic whitespace-separated tokens, with upper-case letters
    #   occurring only as the first character in a token.

    def looks_like_sent (self, s):
        for word in s.split():
            if not word.isalpha(): return False
            elif not (word.islower() or word.istitle()): return False
        return True

    ##  Parse the given sentence.

    def parse (self, s):
        sent = Sent(self, None, s.split())
        sent.parse()
        return sent

    ##  Save translations.

    def save_translations (self):
        fn = self.prefix + '-trans.txt'
        out = open(fn, 'w')
        for sent in self.sents:
            out.write('%d %s\n' % (sent.i, sent.sem))
        out.close()

    ##  Turn on tracing.  One may specify what to trace: 'parse', 'unif',
    #   a particular rule specified by number.

    def trace (self, args=['parse']):
        value = True
        for arg in args:
            if arg == 'on': value = True
            elif arg == 'off': value = False
        for arg in args:
            if arg == 'parse':
                self.trace_parse = value
                print('Trace parse =', self.trace_parse)
            elif arg == 'unif':
                seal.avs.TraceOn = value
            elif arg.isdigit():
                if self.parser is None:
                    print('** No parser')
                elif value:
                    self.parser.trace_rule = int(arg)
                    print('Trace rule', arg)
                elif self.parser.trace_rule == int(arg):
                    self.parser.trace_rule = None
                    print('Trace rule', arg, 'off')
            elif arg not in ['on', 'off']:
                print('** Usage: on off parse unif')

    ##  Print usage message.

    def usage (self):
        print('COMMANDS:')
        print('ls          List the grammars')
        print('r           Reload the grammar and sentences, and reparse')
        print('n           Next: go forward one sentence')
        print('p           Previous: go back one sentence')
        print('(a number)  Go to the sentence with that number')
        print('(a grammar) Load the grammar')
        print('(an expr)   Evaluate the expression in the model')
        print('(sentence)  Parse and evaluate a temporary sentence')
        print('c           Print current sentence (discard temp sent, if any)')
        print('g           Print the grammar')
        print('m           Print the model')
        print('s           Print the sentences')
        print('t           Save the translations to %s-trans.txt' % self.prefix)
        print('h           Print this message')
        print('^D          Quit')

    ##  Execute a command.

    def com (self, com):
        if com == 'h' or com == '' or com == '?':
            self.usage()
        elif com == 'ls':
            self.ls()
        elif com == 'r':
            self.reload()
            self.print_sent()
        elif com == 'c':
            self.tmpsent = None
            self.print_sent()
        elif com == 'p':
            self.step_back()
            self.print_sent()
        elif com == 'n':
            self.step_forward()
            self.print_sent()
        elif com == 'g':
            print(self.grammar)
        elif com == 's':
            self.print_sents()
        elif com == 't':
            self.save_translations()
            print('Wrote translations to %s-trans.txt' % self.prefix)
        elif com == 'm':
            self.print_model()
        elif com == 'trace':
            self.trace()
        elif com.startswith('trace '):
            args = com.split()
            self.trace(args[1:])
        elif com in self.grammars():
            self.prefix = self.grammars()[com]
            self.reload()
        elif com.isdigit():
            self.goto(int(com))
            self.print_sent()
        elif len(com) == 1:
            raise Exception('Unrecognized command')
        elif self.looks_like_sent(com):
            self.tmpsent = self.parse(com)
            self.print_sent()
        else:
            print(self.value(com))

    ##  Run.

    def run (self):
        self.usage()
        while True:
            try:
                print()
                self.com(input('> '))
            except EOFError:
                print()
                break
            except Exception as e:
                print('**', str(e))
                traceback.print_exc()


#--  Sents, Labels  ------------------------------------------------------------

# def save_sents (sents, fn):
#     file = open(fn, 'w')
#     i = 0
#     for sent in sents:
#         file.write('%d %s\n' % (i, ' '.join(sent)))
#         i += 1
#     file.close()

# def load_sents (fn):
#     return list(iter_sents(fn))

# def iter_sents (fn):
#     i = 0
#     for line in open(fn):
#         fields = line.split()
#         if not fields[0].isdigit():
#             raise Exception, "Sents [%d]: line must start with a number" % i
#         if int(fields[0]) != i:
#             raise Exception, "Sents [%d]: lines must be sequentially numbered from zero" % i
#         i += 1
#         yield fields[1:]


# def load_labels (fn):
#     return list(iter_labels(fn))
# 
# def iter_labels (fn):
#     i = 0
#     for line in open(fn):
#         fields = line.split()
#         if len(fields) < 1:
#             raise Exception, "Labels [%d]: empty line" % i
#         if not fields[0].isdigit():
#             raise Exception, "Labels [%d]: line must start with a number" % i
#         if int(fields[0]) != i:
#             raise Exception, "Labels[ %d]: lines must be sequentially numbered from zero" % i
#         i += 1
#         if len(fields) != 2:
#             raise Exception, "Labels [%d]: label must be a single word" % i
#         yield fields[1]


# #--  Grammar  ------------------------------------------------------------------
# 
# def parser_predictions (p, sents):
#     return list(iter_parser_predictions(p, sents))
# 
# def iter_parser_predictions (p, sents):
#     for sent in sents:
#         try:
#             if p(sent):
#                 yield 'OK'
#             else:
#                 yield '*'
#         except:
#             yield '*'
# 
# 
# #--  Scoring  ------------------------------------------------------------------
# 
# def compare_labels (labels, pred):
#     tp = 0
#     fp = 0
#     tn = 0
#     fn = 0
#     for l, p in zip(labels, pred):
#         if l == 'OK':
#             if p == 'OK': tp += 1
#             else: fn += 1
#         else:
#             if p == 'OK': fp += 1
#             else: tn += 1
#     good_sents = tp + fn
#     bad_sents = tn + fp
#     n = good_sents + bad_sents
#     return tp, tn, good_sents, bad_sents, n
# 
# def print_score (labels, pred):
#     tp, tn, good_sents, bad_sents, n = compare_labels(labels, pred)
# 
#     print 'Accuracy:    ',
#     if n > 0: print '%0.6f (%d/%d)' % ((tp + tn)/n, tp + tn, n)
#     else: print '(undefined)'
# 
#     print 'Sensitivity: ',
#     if good_sents > 0: print '%0.6f (%d/%d)' % (tp/good_sents, tp, good_sents)
#     else: print '(undefined)'
# 
#     print 'Specificity: ',
#     if bad_sents > 0: print '%0.6f (%d/%d)' % (tn/bad_sents, tn, bad_sents)
#     else: print '(undefined)'
# 
# def print_errors (sents, labels, pred):
#     i = 0
#     for sent, lab, plab in zip(sents, labels, pred):
#         if lab != plab:
#             print i, lab, ' '.join(sent)
#         i += 1
# 
# 
# #--  Dev  ----------------------------------------------------------------------
# 
# def run ():
#     name = raw_input('grammar name: ')
#     Dev(name).interact()
# 
# 
# class Dev (object):
# 
#     def __init__ (self, name):
#         self.__prefix = Fn(name)
#         self.__parser = None
#         self.__sents = None
#         self.__labels = None
#         self.__pred = None
# 
#     def parser (self):
#         if not self.__parser:
#             self.__parser = Parser(self.__prefix + '.g')
#         return self.__parser
#         
#     def grammar (self):
#         return self.parser().grammar
# 
#     def load_sents (self):
#         self.__sents, self.__labels = load_sents(self.__prefix + '.sents')
# 
#     def sents (self):
#         if not self.__sents: self.load_sents()
#         return self.__sents
# 
#     def labels (self):
#         if not self.__labels: self.load_sents()
#         return self.__labels
# 
#     def reload (self):
#         if self.__parser: self.__parser.reload()
#         else: self.__parser = Parser(self.__prefix + '.g')
#         self.load_sents()
# 
#     def run (self):
#         self.reload()
#         self.__pred = parser_predictions(self.__parser, self.__sents)
#         print_errors(self.__sents, self.__labels, self.__pred)
#         print_score(self.__labels, self.__pred)
# 
#     def parse (self, sent):
#         p = self.parser()
#         return p(sent)
# 
#     def chart (self):
#         return Chart(self.parser())
# 
#     def print_sents (self):
#         sents = self.sents()
#         labels = self.labels()
#         for i, (label, sent) in enumerate(zip(labels, sents)):
#             print i, label, ' '.join(sent)
# 
#     def __getitem__ (self, i):
#         sent = self.sents()[i]
#         label = self.labels()[i]
#         return DevEntry(self, i, sent, label)
# 
#     def interact (self):
#         try:
#             self.run()
#         except Exception, e:
#             print '**', str(e)
#         while True:
#             try:
#                 com = raw_input('> ')
#                 if com == '' or com == 'r': self.run()
#                 elif com == 'g': print self.parser().grammar
#                 elif com[0].isdigit():
#                     i = int(com)
#                     print i
#                     print self[i]
#                 elif com == 'l': self.print_sents()
#                 else:
#                     print 'Type one of: r'
#             except EOFError:
#                 break
#             except Exception, e:
#                 print '**', str(e)
# 
# 
# 
# def cmp_nodes (n1, n2):
#     if   n1.j < n2.j: return -1
#     elif n1.j > n2.j: return +1
#     elif n1.i > n2.i: return -1
#     elif n1.i < n2.i: return +1
#     else: return cmp(n1.cat, n2.cat)
# 
# 
# class Chart (object):
# 
#     def __init__ (self, parser):
#         self.sent = parser.words
#         self.contents = parser.chart
# 
#     def __str__ (self):
#         lines = []
#         for node in sorted(self.contents.itervalues(), cmp=cmp_nodes):
#             txt = ' '.join(self.sent[node.i:node.j])
#             lines.append('[%d:%d] %-20s %s' % (node.i, node.j, node.cat, txt))
#         return '\n'.join(lines)


#--  Main  ---------------------------------------------------------------------

##  Instantiate Dev and run it.

def main ():
    dev = Dev()
    dev.run()

if __name__ == '__main__':
    main()
