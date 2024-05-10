##  @package seal.nlp.dp.parser
#   Generic classifier-based dependency parser.

from ..cld.seal.io import tabular
from ..cld.seal.misc import trim
from ..nlp.dep import Sentence, Word
from .ml.instance import Instance


#--  Configuration  ------------------------------------------------------------

# NoWord = (None, '', '', '', '', '', None, '', None, '')

def _str (s):
    if s is None: return ''
    else: return str(s)


##  A parse node.

class Node (object):

    ##  Constructor.

    def __init__ (self, index=None, source=None):
        if source is None:
            assert index is not None

            ##  The current input index.
            self.index = index

            ##  The governor.
            self.govr = None

            ##  The role.
            self.role = None

            ##  The leftmost child.
            self.lc = None

            ##  The rightmost child.
            self.rc = None

            ##  The left sibling.
            self.ls = None

            ##  The right sibling
            self.rs = None

        else:
            assert index is None
            self.index = source.index
            self.govr = source.govr
            self.role = source.role
            self.lc = source.lc
            self.rc = source.rc
            self.ls = source.ls
            self.rs = source.rs


##  A parse configuration.

class Configuration (object):

    ##  Constructor.

    def __init__ (self, words=None, source=None):
        if source:
            assert words is None

            ##  Of this configuration.
            self.index = source.index + 1

            ##  The source for the input.
            self.source = source

            ##  Input sentence.
            self.sent = source.sent

            ##  Input words.
            self.words = source.words

            ##  Input pointer (into self.words).
            self.pointer = source.pointer

            self._stack = source._stack
            self._nodes = source._nodes

        elif words:
            self.source = None
            self.index = 0
            if isinstance(words, Sentence):
                self.sent = words
                self.words = [words.form(i) for i in range(len(words))]
            else:
                self.sent = None
                self.words = ['*root*'] + words
            self.pointer = 1
            self._stack = [0]
            self._nodes = [Node(i) for i in range(len(self.words))]

        else:
            raise Exception('Must provide words or source')

    ##  The sentence provenance, if there is one.

    def provenance (self):
        if self.sent:
            return '%s.%d' % (self.sent.provenance(), self.index)
        else:
            return ''

    ##  The t-th input word (relative to the current pointer).

    def input (self, t):
        if t < 0: return None
        i = self.pointer + t
        if i < 0 or i >= len(self.words): return None
        else: return i

    ##  The t-th word on the stack.

    def stack (self, t):
        if t < 0 or t >= len(self._stack): return None
        else: return self._stack[-(t+1)]

    #--  Word properties  ------------------

    ##  The w-th word.  (Implements a feature.)

    def word (self, w):
        if w is not None:
            return self.words[w]

#    def features (self, w):
#        assert self.sent
#        if w is None: return NoWord
#        return self.sent[w]

    ##  The lemma of word w.  (Implements a feature.)

    def lemma (self, w):
        if w: return self.sent.lemma(w)

    ##  Coarse POS of word w.  (Implements a feature.)

    def cpos (self, w):
        if w:
            cat = self.sent.cat(w)
            if isinstance(cat, tuple): return cat[0]
            else: return cat

    ##  Fine-grained POS of word w.

    def fpos (self, w):
        if w:
            cat = self.sent.cat(w)
            if isinstance(cat, tuple): return cat[1]
            else: return cat

    ##  Morph feature of word w.

    def morph (self, w):
        if w: return self.sent.morph(w)

    ##  True governor of word w.

    def true_govr (self, w):
        assert self.sent
        if w: return self.sent.govr(w)

    ##  True role of word w.

    def true_role (self, w):
        assert self.sent
        if w: return self.sent.role(w)
        else: return ''

    ##  Governor of word w.

    def govr (self, w):
        if w: return self._nodes[w].govr

    ##  Role of word w.

    def role (self, w):
        if w: return self._nodes[w].role

    ##  Leftmost child of word w.

    def lc (self, w):
        if w: return self._nodes[w].lc

    ##  Rightmost child of word w.

    def rc (self, w):
        if w: return self._nodes[w].rc

    ##  Left sibling of word w.

    def ls (self, w):
        if w: return self._nodes[w].ls

    ##  Right sibling of word w.

    def rs (self, w):
        if w: return self._nodes[w].rs

    ##  Whether word w has its governor and all its dependents.

    def is_complete (self, w):
        if self.govr(w) is None: return False
        for i in range(self.pointer, len(self.words)):
            if self.true_govr(i) == w and self.govr(i) is None:
                return False
        return True

    #--  Actions  --------------------------

    def _node (self, w):
        node = self._nodes[w]
        if self.source:
            if self._nodes is self.source._nodes:
                self._nodes = self._nodes[:]
            if node is self.source._nodes[w]:
                node = Node(source=node)
                self._nodes[w] = node
        return node

    def _push (self, w):
        self._stack = self._stack + [w]

    def _pop (self):
        assert len(self._stack) > 1
        self._stack = self._stack[:-1]

    # g d
    # d.govr = g
    # set d.role
    # d.ls = g.rc
    # g.rc.rs = d
    # g.rc = d

    ##  Attach input[0] to stack[0].  Move input[0] onto the stack.

    def attach_left (self, role):
        out = Configuration(source=self)
        g = out.stack(0)
        d = out.input(0)
        gn = out._node(g)
        dn = out._node(d)
        assert dn.govr is None
        dn.govr = g
        dn.role = role
        dn.ls = gn.rc
        if gn.rc:
            lsn = out._node(gn.rc)
            lsn.rs = d
        gn.rc = d
        out._push(d)
        out.pointer += 1
        return out

    ##  Attach stack[0] to input[0].  Pop the stack.

    def attach_right (self, role):
        out = Configuration(source=self)
        d = out.stack(0)
        g = out.input(0)
        dn = out._node(d)
        gn = out._node(g)
        assert dn.govr is None
        dn.govr = g
        dn.role = role
        dn.rs = gn.lc
        if gn.lc:
            rsn = out._node(gn.lc)
            rsn.ls = d
        gn.lc = d
        out._pop()
        return out

    ##  Move input[0] onto the stack.

    def shift (self):
        out = Configuration(source=self)
        w = out.input(0)
        assert w
        out._push(w)
        out.pointer += 1
        return out

    ##  Pop the stack.

    def reduce (self):
        out = Configuration(source=self)
        out._pop()
        return out

    #--  Call  -----------------------------
    
    ##  Call an action: 'al' for attach_left(), 'ar' for attach_right(), 're' for 
    #   reduce(), 'sh' for shift().

    def __call__ (self, action, role=None):
        if action == 'al':
            return self.attach_left(role)
        elif action == 'ar':
            return self.attach_right(role)
        elif action == 're':
            assert role is None
            return self.reduce()
        elif action == 'sh':
            assert role is None
            return self.shift()
        else:
            raise Exception('Unrecognized action: ' + repr(action))

    ##  Whether the named action is permissible.

    def is_permissible (self, action):
        if self.pointer >= len(self.words):
            return False
        if action == 'ar':
            d = self.stack(0)
            return d and self.govr(d) is None
        elif action == 'al':
            d = self.input(0)
            return d and self.govr(d) is None
        elif action == 're':
            w = self.stack(0)
            return w and self.govr(w) is not None
        elif action == 'sh':
            return True
        else:
            raise Exception('Unrecognized action: ' + repr(action))

    ##  Whether there is any remaining input.

    def can_continue (self):
        return self.pointer < len(self.words)

    #--  Sentence  -------------------------

    ##  Construct a sentence.

    def sentence (self):
        assert self.sent
        out = Sentence(index=self.sent.index())
        for w in range(1, len(self.sent)):
            word = self.sent[w]
            govr = self.govr(w) or 0
            role = self.role(w) or ''
            out.append(Word(w, word.form, word.cat,
                            word.lemma, word.morph,
                            govr, role))
        return out

    #--  Print  ----------------------------

    ##  Returns a string depicting what is on the stack.

    def buffer_string (self):
        buf = []
        for i in range(len(self._stack)):
            w = self._stack[i]
            buf.append(trim(2, self.words[w]))
        buf.append('|')
        for w in range(self.pointer, len(self.words)):
            buf.append(trim(2, self.words[w]))
        return ' '.join(buf)

    ##  Detailed string representation.

    def __str__ (self):
        r = list(range(len(self.words)))
        rows = []
        if self.sent:
            true_govrs = [_str(self.true_govr(i)) for i in r]
            true_roles = [_str(self.true_role(i)) for i in r]
            rows.append(['    tgovr:'] + true_govrs)
            rows.append(['    trole:'] + [trim(2,role) for role in true_roles])
        govrs = []
        roles = []
        for node in self._nodes:
            roles.append(_str(node.role))
            govrs.append(_str(node.govr))
        rows.append(['    govr:'] + govrs)
        rows.append(['    role:'] + [trim(2,role) for role in roles])
        if self.sent:
            rows.append(['    cpos:'] + [trim(2, self.cpos(i)) for i in r])
            rows.append(['    fpos:'] + [trim(2, self.fpos(i)) for i in r])
        rows.append(['    form:'] + [trim(2,word) for word in self.words])
        rows.append(['    i:'] + r)
        deco = ['']
        for w in r:
            if w == self.pointer: deco.append('|-')
            elif w in self._stack: deco.append('*')
            else: deco.append('')
        rows.append(deco)
        out = tabular(rows)
        prov = self.provenance() or ''
        if prov: prov = ' ' + prov
        return 'Configuration%s:\n%s' % (prov, out)
#            '    stack: ' + ' '.join(str(elt) for elt in self._stack) + '\n' + \
#            '    pointer: ' + str(self.pointer) + \
#            '\n' + out


##  Return a list of configurations.

def computation (sent, orc, strict=False, trace=False):
    return list(itercomputation(sent, orc, strict=strict, trace=trace))

##  Iterate over computations.

def itercomputation (sent, orc, strict=False, trace=False):
    c = Configuration(sent)
    if trace: print(c)
    while c.can_continue():
        (act, role) = orc(c)
        if trace:
            print()
            print('=>', act, role)
        if not c.is_permissible(act):
            if strict:
                raise Exception('Oracle output impermissible')
            if trace: print('=> Substituting sh')
            act = 'sh'
            role = None
        yield (c, act, role)
        c = c(act, role)
        if trace:
            print()
            print(c)
    yield (c, 'stop', None)

##  Print a given computation.

def print_computation (comp):
    for (cfg, act, role) in comp:
        print(cfg.buffer_string())
        print(' ->', act, role)

##  Print a detailed description of a computation.

def dump_computation (comp, featurefnc=None):
    cfg = comp[0][0]
    if cfg.sent:
        print(cfg.sent)
    else:
        print(cfg.sent)
    for (cfg, act, role) in comp:
        print()
        print(cfg)
        if featurefnc:
            print()
            print(Instance(label=encode_label(act,role), ftrs=featurefnc(cfg)))
        else:
            print()
            print('=>', act, role)


#--  Supervised oracle  --------------------------------------------------------

#  buffer = ... L | R ...
#  if R doesn't exist, stop
#  if R true governor is L, and R is unattached, then attach-left
#  if L true governor is R, and L is unattached, then attach-right
#  if L is attached and no word in R... is governed by L, then reduce
#  otherwise, shift

##  What to do next in order to construct the manual parse.
#   Return value is a pair (act, role) suitable as input to
#   the configuration's __call__() method.

def supervised_oracle (config):
    assert config.sent
    l = config.stack(0)
    r = config.input(0)
    if r is None: raise Exception('Oracle invoked on dead configuration')
    la = config.govr(l)
    ra = config.govr(r)
    if ra is None and config.true_govr(r) == l:
        act = 'al'
        role = config.true_role(r)
    elif la is None and config.true_govr(l) == r:
        act = 'ar'
        role = config.true_role(l)
    elif config.is_complete(l):
        act = 're'
        role = None
    else:
        act = 'sh'
        role = None
    if not config.is_permissible(act):
        raise Exception('Not permissible: %s %s' % (act, role))
    return (act, role)

##  Encode a label.

def encode_label (act, role):
    if role: return '%s_%s' % (act, role)
    else: return act

##  Decode a label.  Return is a pair (act, role).

def decode_label (label):
    if label in ['re', 'sh']: return (label, None)
    elif label in ['ar', 'al']: return (label, '')
    else:
        if not (len(label) >= 3 and label[2] == '_'):
            raise Exception('Bad label: ' + str(label))
        act = label[:2]
        role = label[3:]
        assert act in ['al', 'ar']
        return (act, role)

##  Iterate over instances using supervised oracle.

def iterinstances (sents, ftrfnc, strict=True):
    if isinstance(sents, Sentence): sents = [sents]
    for sent in sents:
        for (cfg, act, role) in computation(sent, supervised_oracle, strict=strict):
            if act != 'stop':
                ftrs = ftrfnc(cfg)
                yield Instance(orig=cfg, label=encode_label(act, role), ftrs=ftrs)

##  List of instances.

def instances (sents, ftrfnc):
    return list(iterinstances(sents, ftrfnc))

##  Simple features.

def simple_features (c):
    return [('s2', c.word(c.stack(1))),
            ('s1', c.word(c.stack(0))),
            ('la1', c.word(c.input(0))),
            ('la2', c.word(c.input(1)))]


#--  Classifier oracle  --------------------------------------------------------

##  Classifier oracle.

class ClassifierOracle (object):

    ##  Constructor.

    def __init__ (self, classifier, ftrfnc):

        ##  The prediction function.
        self.predict = classifier

        ##  The feature function.
        self.getfeatures = ftrfnc

    ##  Call the oracle on a configuration.  Returns a pair (act, role).

    def __call__ (self, config):
        ftrs = self.getfeatures(config)
        label = self.predict(ftrs)
        return decode_label(label)


#--  Parse  --------------------------------------------------------------------

##  Parser.

class Parser (object):

    ##  Constructor.

    def __init__ (self, oracle):

        ##  An oracle.
        self.oracle = oracle

    ##  Apply it to a sentence.  Just a wrapper around computation().
    #   Uses Configuration.sentence() to unwind the results.

    def __call__ (self, sent, trace=False):
        comp = computation(sent, self.oracle, trace=trace)
        cfg = comp[-1][0]
        return cfg.sentence()
