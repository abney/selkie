##  \package seal.nlp.head
#   Heuristic head-identification rules.

import os
from os.path import join
from .data import path
from .io import iter_records
from .tree import head_child, is_leaf, getcat, getchildren, getnld, Tree, nodes


#--  Head rules  ---------------------------------------------------------------

##  Converts an unheaded phrase-structure tree to a headed phrase-structure tree.
#   Expects a consistent phrase-structure tree.  Will not change any existing heads.
#   A node marked as head loses whatever role it previously had.

def mark_heads (node, headrules=None):
    children = getchildren(node)
    if children:
        for child in children:
            mark_heads(child, headrules)
        nld = getnld(node)
        if nld is None and not head_child(node):
            h = find_head(node, headrules)
            children[h].role = 'head'

##  Find the head for a given node.

def find_head (node, headrules=None, trace=False):
    global DefaultHeadRules
    if headrules is None: headrules = DefaultHeadRules
    return headrules.find_head(getcat(node), getchildren(node), trace)

    
##  A head-assignment rule.

class HeadRule:

    ##  Constructor.
    
    def __init__ (self, parent, index, dir, cats):

        ##  Parent specification.
        self.parent = parent

        ##  The rule number.
        self.index = index

        ##  The direction of search: either L (left-to-right) or R (right-to-left).
        self.dir = dir

        ##  The categories that the rule matches on.
        self.cats = cats

    ##  Returns a range to use to iterate through a node's children,
    #   where n is the number of children.  If the rule direction is L,
    #   the range is [0...n-1], and if R, [n-1...0].

    def range (self, n):
        if self.dir == "L": return list(range(n))
        else: return list(range(n-1, -1, -1))
    
    ##  String representation.

    def __str__ (self):
        return str(self.index) + ' ' + self.dir + ': ' + ' '.join(self.cats)
    
    ##  String representation.

    def __repr__ (self):
        return '<Rule %s %d>' % (self.parent, self.index)


##  A collection of head-assignment rules,
#   implementing Magerman-Collins style rules.
#   Calling the constructor with no arguments uses a default set of rules.
#   (They are not the same as the original Magerman-Collins rules.)
#   One can use an alternative set of rules by calling the constructor with a file as
#   argument.

class HeadRules(object):

    ##  Returns the last child of this node, if it is a terminal and possible head.

    def last_word (self, chcats, children):
        if children:
            for i in range(len(children)-1, 0, -1):
                if is_leaf(children[i]) and chcats[i] not in self.nonhead_categories:
                    return i
        return None

    ##  Constructor.

    def __init__ (self, fn=None):

        ##  Filename.
        self.filename = fn

        ##  List of rules.
        self.rules = None

        ##  NP rules.
        self.nprules = None

        ##  Nonhead categories.
        self.nonhead_categories = set()


    ##  Load a set of head rules from file.  The fn is actually a prefix:
    #   the files fn_main.txt and fn_np.txt should both exist.

    def load (self):
        self.rules = {}
        self.nprules = []
        tf = iter_records(str(self.filename) + "_main.txt")
        for record in tf:

            if len(record) == 2 and record[0] == 'non heads:':
                for cat in record[1].split(" "):
                    self.nonhead_categories.add(cat)

            elif len(record) == 3:
                parent = record[0]
                if parent == "NP": tf.error("NP rules belong in separate file")
                dir = record[1]
                cats = record[2].split(" ")
                if parent in self.rules:
                    rules = self.rules[parent]
                else:
                    rules = []
                    self.rules[parent] = rules
                rule = HeadRule(parent, len(rules), dir, cats)
                rules.append(rule)

            else:
                tf.error("Bad record: " + str(record))

        tf = iter_records(str(self.filename) + "_np.txt")
        for record in tf:
            if len(record) != 2: tf.error("Wrong number of fields")
            dir = record[0]
            cats = record[1].split(" ")
            rule = HeadRule('NP', len(self.nprules), dir, cats)
            self.nprules.append(rule)

    ##  Content listing as a string.

    def __str__ (self):
        lines = ['Non-head cats: ' + ' '.join(cat for cat in self.nonhead_categories)]
        for cat in self.rules:
            lines.append(cat)
            for rule in self.rules[cat]:
                lines.append('    ' + str(rule))
        lines.append('NP')
        for rule in self.nprules:
            lines.append('    ' + str(rule))
        return '\n'.join(lines)


    ##  Find the head of this local tree.
    #   Returns a head index for node, or None if the node has no children.
    #   There is guaranteed to be a head index for any interior node.

    def find_head (self, cat, children, trace=False):
        if not (self.rules or self.nprules):
            self.load()

        if not children:
            if trace: print('No children: no head')
            return None

        pcat = str(cat)
        chcats = [str(child.cat) for child in children]
        h = self.__find_head_1(pcat, chcats, children, trace)

        ##  Coordination adjustment
        if h >= 2 \
                and chcats[h-1] == "CC" \
                and chcats[h-2] not in self.nonhead_categories:
            h = h-2
            if trace: print('Coord adjust (-2): h=' + str(h))
        elif h >= 3 \
                and chcats[h-1] == "CC" \
                and chcats[h-2] == ',' \
                and chcats[h-3] not in self.nonhead_categories:
            h = h-3
            if trace: print('Coord adjust (-3): h=' + str(h))

        return h

    def __find_head_1 (self, pcat, chcats, children, trace=False):

        if pcat == "NP":
            lw = self.last_word(chcats, children)
            if lw != None and chcats[lw] == "POS":
                if trace: print('NP, lw == POS: h=%d' % lw)
                return lw
            for rule in self.nprules:
                rng = rule.range(len(chcats))
                for i in rng:
                    for cat in rule.cats:
                        if chcats[i] == cat:
                            if trace: print('Rule %s, found %s: h=%d' % (repr(rule), cat, i))
                            return i
            if lw != None:
                if trace: print('NP, no rule matches, lw exists: h=%d' % lw)
                return lw
            else:
                if trace: print('NP, no rule matches, no lw, resorting to default rule')
                return self.default_head(chcats, trace)

        elif pcat in self.rules:
            for rule in self.rules[pcat]:
                rng = rule.range(len(chcats))
                for cat in rule.cats:
                    for i in rng:
                        if chcats[i] == cat:
                            if trace: print('Rule %s, found %s: h=%d' % (repr(rule), cat, i))
                            return i
            for i in rng:
                if chcats[i] not in self.nonhead_categories:
                    if trace: print('No rule matches, possible head: h=%d' % i)
                    return i
            
            if trace: print('Last resort, guessing first: h=0')
            return rng[0]

        else:
            if trace: print('Unknown category, resorting to default rule')
            return self.default_head(chcats, trace)

    ##  The default rule.

    def default_head (self, chcats, trace=False):
        for i in range(len(chcats)-1, -1, -1):
            if chcats[i] not in self.nonhead_categories:
                if trace: print('Possible head %s: h=%d' % (chcats[i], i))
                return i
        if trace: print('Last result, guessing last: h=%d' % (len(chats) - 1))
        return len(chcats) - 1


##  The default rules.
DefaultHeadRules = HeadRules(path('selkie', 'headrules'))

##  The original Magerman-Collins rules.
CollinsMagermanRules = HeadRules(path('selkie', 'original_headrules'))


#--  Decoordination  -----------------------------------------------------------

##  Undoes coordination.
#
#       X1 , X2 CC X3    ->    X1 [CO:co , X2 ] [CO:co CC X3 ]
#

class Decoordinator (object):

    ##  Constructor.

    def __init__ (self, cc='CC', co='CO', corole='co', connectors=False):
        if connectors is False: connectors = [',', ';']

        ##  The CC category.
        self.cc = cc

        ##  The CO category.
        self.co = co

        ##  The coordination role.
        self.corole = corole

        ##  By default, comma and semicolon.
        self.connectors = set(connectors)

        ##  Not used?
        self.j = -1

        ##  Children.
        self.children = None

    ##  Whether the i-th child is a connector.

    def is_connector (self, i):
        if i < 0 or i >= len(self.children): return False
        return self.children[i].cat in self.connectors

    ##  Whether the i-th child is a coordinator.

    def is_cc (self, i):
        if i < 0 or i >= len(self.children): return False
        return self.children[i].cat == self.cc

    ##  Whether the i-th child is a possible coordinand.

    def is_possible_coordinand (self, i):
        if i < 0 or i >= len(self.children): return False
        node = self.children[i]
        return (node.cat[0].isalpha() and
                node.cat != self.cc and
                node.cat != self.co)

    ##  Input j is the index of a CC.  Looks if there is a match of form:
    #
    #       Possible ( Connector Possible )* Connector? CC Possible.
    #
    #   If so, returns beginning position.

    def match_at (self, j):
        if not self.is_possible_coordinand(j+1): return -1
        i = j - 1
        if self.is_connector(i): i -= 1
        if not self.is_possible_coordinand(i): return -1
        i -= 1
        while self.is_connector(i-1) and self.is_possible_coordinand(i-2):
            i -= 2
        return i

    ##  Finds the rightmost match for the pattern:
    #
    #       Possible ( Conn Possible )* Conn? CC Possible
    #
    #   Returns (i,j) with i inclusive, j exclusive; or None.

    def match (self, node):
        self.children = getchildren(node)
        if self.children is None: return None
        for j in range(len(self.children)-1, -1, -1):
            if self.is_cc(j):
                i = self.match_at(j)
                if i >= 0: return (i, j+2)
        return None

    ##  Takes the match (i,j) returned by self.match(node).
    #   Excises the match X and replaces it with [CO X ].
    #   The last node in the match is the head of CO.

    def apply (self, match, node):
        if not node.nld is None: raise Exception("Cannot handle governor")
        (i, j) = match
        excised = node.children[i:j]
        excised[-1].role = 'head'
        coordinand = Tree(cat=self.co, role=self.corole, children=excised)
        node.children[i:j] = [coordinand]
            
    ##  Call it on a node.

    def __call__ (self, node):
        while True:
            m = self.match(node)
            if m is None: break
            self.apply(m, node)


##  An instance of Decoordinator.
decoordinate_node = Decoordinator()

##  Decoordinate all nodes in a given tree.

def decoordinate (tree):
    for node in nodes(tree):
        decoordinate_node(node)


#--  cc heads  -----------------------------------------------------------------

##  Mark_heads() treats the first coordinand as head.  This behavior can be
#   overridden by premarking cc nodes as heads, which is what mark_cc_heads()
#   does.

def mark_cc_heads (tree):
    for node in nodes(tree):
        mark_cc_head(node)

##  Mark the cc head of this node, if it has one.

def mark_cc_head (node):
    if node.children:
        for child in node.children:
            if child.cat == 'CC':
                child.role = 'head'
                break
