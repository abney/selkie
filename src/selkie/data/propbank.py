##  @package seal.data.propbank
#   Propbank.

import seal.data.ptb as ptb
from seal.nlp.dep import mark_heads


##  The data directory.
data_dir = '/cl/data/propbank_1/data/'


######################################################################
#                                                                    #
#  The raw propbank file (prop.txt)                                  #
#                                                                    #
######################################################################

##  The raw entries.  Use raw_entries() instead.
RawEntries = None

##  Return the raw entries.  Loads and caches them the first time it is called.

def raw_entries ():
    global RawEntries
    if RawEntries == None:
        RawEntries = []
        for line in open(data_dir + 'prop.txt'):
            RawEntries.append(parse_line(line))
    return RawEntries


##  Parse a line of the input file.

def parse_line (line):
    fields = line.split()
    fn = fields[0]
    fileid = ptb.fileid_from_orig(fn)
    sentnum = int(fields[1])
    verb_leafnum = int(fields[2])
    tagger = fields[3]
    frameset = fields[4]
    inflection = fields[5]
    args = [parse_arg(fields[i]) for i in range(6, len(fields))]
    return (fileid, fn, sentnum, verb_leafnum, tagger, frameset, inflection, args)

##  Called by parse_line().

def parse_arg (arg):
    fields = arg.split('-')
    loc = parse_location(fields[0])
    label = fields[1]
    if len(fields) > 2:
        role = fields[2]
    else:
        role = None
    return (loc, label, role)

##  Called by parse_arg().

def parse_location (loc):
    return [parse_element(elt) for elt in loc.split('*')]

##  Called by parse_location().

def parse_element (elt):
    return [parse_nodeaddr(a) for a in elt.split(',')]

##  Called by parse_element().

def parse_nodeaddr (addr):
    fields = addr.split(':')
    return (int(fields[0]), int(fields[1]))


######################################################################
#                                                                    #
#  Digesting a treebank file                                         #
#                                                                    #
######################################################################


##  A file in the treebank.

class File (object):

    ##  Constructor.

    def __init__ (self, id):

        ##  The file ID.
        self.fileid = id

        ##  The corresponding filename in the Penn Treebank.
        self.filename = ptb.orig_filename(id)

        trees = ptb.trees(self.fileid)
        for tree in trees:
            mark_heads(tree)
            index(tree)
            add_spans(tree)

        ##  The contents, a list of Sentence instances.
        self.sentences = [Sentence(self, i, trees[i]) for i in range(len(trees))]

    ##  Add a new entry.

    def append (self, entry):
        if entry.fileid != self.fileid: raise Exception("Not my entry")
        i = entry.sentence_number
        if i < 0 or i >= len(self.sentences): raise Exception("Bad sentence number")
        s = self.sentences[i]
        s.append(entry)
        entry.finish_init(self, s)

    ##  Iterates over all entries.

    def all_entries (self):
        for sent in self.sentences:
            for entry in sent.entries:
                yield entry

    ##  Fetch a sentence by index.

    def __getitem__ (self, i):
        return self.sentences[i]


##  A sentence.

class Sentence (object):

    ##  Constructor.

    def __init__ (self, file, n, tree):

        ##  The file.
        self.file = file

        ##  Where it is in the file.
        self.index = n

        ##  The parse tree.
        self.tree = tree

        ##  The word entries.
        self.entries = []

    ##  Add a new word entry.

    def append (self, entry):
        if entry.sentence_number != self.index: raise Exception("Not my entry")
        self.entries.append(entry)
        
    ##  Fetch a word entry by index.

    def __getitem__ (self, i):
        return self.entries[i]


##  A word entry.

class Entry (object):

    ##  Constructor.

    def __init__ (self, raw):

        ##  The file ID.
        self.fileid = raw[0]

        ##  The pathname.
        self.filename = raw[1]

        ##  The sentence index.
        self.sentence_number = raw[2]

        ##  The verb number.
        self.verb_leaf_number = raw[3]

        ##  The annotator's code.
        self.annotator = raw[4]

        ##  The frameset.
        self.frameset = raw[5]

        ##  The inflection.
        self.inflection = raw[6]

        ##  Raw input.
        self.raw_args = raw[7]

        ##  Digested args.
        self.args = None

        ##  The file.
        self.file = None

        ##  The sentence.
        self.sentence = None

    ##  Set the file, sentence, and digested args.

    def finish_init (self, file, sent):
        self.file = file
        self.sentence = sent
        self.args = [Arg(c, t, r, self.sentence.tree) for c,t,r in self.raw_args]

    ##  Readable details.

    def __str__ (self):
        args_str = ''
        for i, arg in enumerate(self.args):
            args_str += "\n    [%2d]:           %s" % (i, arg)
        return "Entry:" \
            + "\n  filename:         " + self.filename \
            + "\n  fileid:           " + str(self.fileid) \
            + "\n  sentence_number:  " + str(self.sentence_number) \
            + "\n  verb_leaf_number: " + str(self.verb_leaf_number) \
            + "\n  annotator:        " + self.annotator \
            + "\n  frameset:         " + self.frameset \
            + "\n  inflection:       " + self.inflection \
            + "\n  args:             " + args_str


##  An argument.

class Arg (object):

    ##  Constructor.

    def __init__ (self, chain, argtype, role, tree):

        ##  The chain it belongs to.
        self.chain = [MultiNode(s,tree) for s in chain]

        ##  The argument type.
        self.argtype = argtype

        ##  The role.
        self.role = role

    ##  String representation.

    def __str__ (self):
        s = self.argtype
        if self.role: s += '.' + self.role
        return '[' + '*'.join(str(n) for n in self.chain) + '] ' + s


##  A chain link.

class MultiNode (object):

    ##  Constructor.

    def __init__ (self, elts, tree):

        ##  The elements, a list of pairs (i,h), where i is the node index
        #   and h identifies an element in the node.
        self.elts = elts

        ##  The nodes
        self.nodes = [tree.index[i][h] for i,h in elts]

    ##  String representation.

    def __str__ (self):
        return ' '.join(n.string().replace(' ', '_') for n in self.nodes)

    ##  Whether it is contiguous.

    def is_contiguous (self):
        k = self.nodes[0].span[1]
        for n in self.nodes[1:]:
            if n.span[0] != k: return False
            k = n.span[1]
        return True


##  Iterate over File instances.

def files ():
    entries = raw_entries()
    i = 0

    for fileid in range(2312):
        file = File(fileid)
        while entries[i][0] == fileid:
            file.append(Entry(entries[i]))
            i += 1
        yield file


##  Get a file by ID.

def get_file (fileid):
    for file in files():
        if file.fileid == fileid:
            return file
    raise Exception("Bad fileid")


##  Iterate over word entries.

def entries (fileid=None, sentid=None):
    if fileid == None:
        return all_entries()
    else:
        file = get_file(fileid)
        if sentid == None:
            return file.all_entries()
        else:
            return file[sentid].entries


##  Iterate over all word entries in the corpus.

def all_entries ():
    for file in files():
        for sent in file.sentences:
            for entry in sent.entries:
                yield entry


######################################################################
#                                                                    #
#  Aligning propbank with trees                                      #
#                                                                    #
######################################################################

##  Set tree.index.

def index (tree):
    root = tree.root()
    add_parent_recurse(root, None)
    leaves = root.leaves()
    index = [[] for i in range(len(leaves))]
    for i in range(len(leaves)):
        index[i] = first_child_column(leaves[i])
    tree.index = index

##  Set node.parent for all nodes in the subtree.

def add_parent_recurse (node, parent):
    node.parent = parent
    if node.children():
        for child in node.children():
            add_parent_recurse(child, node)

##  Set node.span for all nodes in the tree.

def add_spans (tree):
    add_spans_1(tree.root(), 0)

##  Helper.

def add_spans_1 (node, i):
    if node.children():
        j = i
        for child in node.children():
            j = add_spans_1(child, j)
    else:
        j = i+1
    node.span = (i,j)
    return j

##  Whether this is the first child of its parent.

def is_first_child (node):
    return node.parent and node.parent.children()[0] == node

##  Returns a list of nodes in which the first node is this one,
#   the i+1st node is the parent of the i-th node, and all except
#   the last one are first children.

def first_child_column (node):
    if is_first_child(node):
        return [node] + first_child_column(node.parent)
    else:
        return [node]

##  This node and all its ancestors.  A list.

def ancestors (node):
    if node.parent:
        return [node] + ancestors(node.parent)
    else:
        return [node]

##  The common prefix of two lists.

def common_prefix (list1, list2):
    n = 0
    len1 = len(list1)
    len2 = len(list2)
    while n < len1 and n < len2 and list1[n] == list2[n]:
        n += 1
    return list1[:n]

##  The common suffix of two lists.

def common_suffix (list1, list2):
    n = 0
    len1 = -len(list1)
    len2 = -len(list2)
    while n > len1 and n > len2 and list1[n-1] == list2[n-1]:
        n -= 1
    return list1[n:]

##  The lowest common ancestor of a set of nodes.

def lowest_common_ancestor (nodes):
    anc = ancestors(nodes[0])
    for node in nodes[1:]:
        anc = common_suffix(anc, ancestors(node))
    return anc[0]

##  The head word of a node.  It is a descendant but not necessarily a child
#   of the node.

def head_leaf (node):
    hc = node.head_child()
    if hc:
        return head_leaf(hc)
    else:
        return node


######################################################################
#                                                                    #
#  Exploration                                                       #
#                                                                    #
######################################################################

##  Check contiguity of chains in the corpus.

def check_contiguity ():
    nchecked = 0
    for f, file in enumerate(files()):
        for s, sent in enumerate(file.sentences):
            for e, entry in enumerate(sent.entries):
                nchecked += 1
                for a, arg in enumerate(entry.args):
                    for k, elt in enumerate(arg.chain):
                        if not elt.is_contiguous():
                            print("noncontig:", f, s, e, a, k, elt)
    print("nchecked:", nchecked)
