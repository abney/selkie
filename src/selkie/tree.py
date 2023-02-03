##  \package seal.nlp.tree
#   Parse trees.

import itertools, os, sys

from .io import StringIO, Fn, tabular, iter_tokens, \
    outfile, close, scanable_string, \
    iter_records, save_records, Syntax

from .string import as_ascii
from .seq import as_list, nth


#--  Tree  ---------------------------------------------------------------------

##  A tree.

class Tree (object):

    ##  Constructor.

    def __init__ (self, cat=None, children=None, word=None, nld=None, role=None, id=None, sem=None):

        ##  Category.
        self.cat = cat

        ##  Children.
        self.children = children

        ##  Word.
        self.word = word

        ##  Role.
        self.role = role

        ##  Number of left dependents.
        self.nld = nld

        ##  ID.
        self.id = id

        ##  Semantics.
        self.sem = sem

    ##  Duplicate it, possibly changing some attributes.

    def copy (self, cat=False, children=False, word=False, nld=False, role=False, id=False, sem=False):
        if cat is False: cat = self.cat
        if children is False:
            children = self.children
            if children: children = list(children)
        if word is False: word = self.word
        if nld is False: nld = self.nld
        if role is False: role = self.role
        if id is False: id = self.id
        if sem is False: sem = self.sem
        return Tree(cat, children, word, nld, role, id, sem)

    ##  Non-recursive string representation.

    def __repr__ (self):

        if self.word: word = ' ' + scanable_string(self.word)
        else: word = ''

        if self.children: children = ' ...'
        else: children = ''

        return "<Tree %s%s%s>" % (str(self.cat), word, children)

    ##  Iterate (pre-order walk).

    def __iter__ (self):
        return preorder(self)

    ##  I-th element in a pre-order walk.  (Pre-order so that it agrees
    #   with the output of __str__().)

    def __getitem__ (self, i):
        return nth(preorder(self), i)

    ##  Pretty-printed string, in parenthesized format.

    def __str__ (self):
        return tree_string(self)

    ##  Pretty-print.

    def pprint (self, file=None):
        if file == None: file = sys.stdout
        file.write(tree_string(self, numerate=False))
        file.write('\n')

    ##  Category.
    def getcat (self): return self.cat

    ##  Children.
    def getchildren (self): return self.children

    ##  Parent.
    def getparent (self): return getparent(self)

    ##  Word.
    def getword (self): return self.word

    ##  Number of left dependents.
    def getnld (self): return self.nld

    ##  Role.
    def getrole (self): return self.role

    ##  ID.
    def getid (self): return self.id

    ##  Semantics.
    def getsem (self): return self.sem

    ##  True if it has children.
    def is_interior (self): return is_interior(self)

    ##  True if it has no children.
    def is_leaf (self): return is_leaf(self)

    ##  True if it has children and a word.
    def is_governor (self): return is_governor(self)

    ##  True if it has children but no word.
    def is_phrase (self): return is_phrase(self)

    ##  True if it has a head child.
    def is_headed_phrase (self): return is_headed_phrase(self)

    ##  True if it has children but not a head child.
    def is_unheaded_phrase (self): return is_unheaded_phrase(self)

    ##  True if it is a leaf and has a word.
    def is_leaf_word (self): return is_leaf_word(self)

    ##  True if it is a leaf but has no word.
    def is_empty_leaf (self): return is_empty_leaf(self)

    ##  True if it has exactly one child.
    def is_unary (self): return is_unary(self)

    ##  Value is one of: LeafType, GovernorType, HeadedPhraseType, UnheadedPhraseType.
    def nodetype (self): return nodetype(self)

    ##  The (first) child whose role is 'head', if any.
    def head_child (self): return head_child(self)

    ##  The position of the (first) child whose role is 'head', or -1 if none do.
    def head_index (self): return head_index(self)

    ##  The position of the given child in the list of children.
    def child_index (self, child): return child_index(self, child)

    ##  If this node has a word, the split between left and right dependents
    #   is determined by nld.  Otherwise, the head child separates the left and right
    #   dependents.
    def left_dependents (self): return left_dependents(self)

    ##  See left_dependents().
    def right_dependents (self): return right_dependents(self)

    ##  The categories of this node and its children.
    def expansion (self): return expansion(self)

    ##  Delete the i-th child.
    def delete_child (self, i): return delete_child(self, i)

    ##  True if all nodes are headed phrases or leaves.
    def is_headed_tree (self): return is_headed_tree(self)

    ##  True if all nodes are unheaded phrases or leaves.
    def is_unheaded_tree (self): return is_unheaded_tree(self)

    ##  True if all node are governors or leaves.
    def is_dependency_tree (self): return is_dependency_tree(self)

    ##  The value is GovernorType, HeadedPhraseType, UnheadedPhraseType, LeafType,
    #   or None.
    def treetype (self): return treetype(self)

    ##  Iteration in pre-order.
    def preorder (self): return preorder(self)

    ##  Iteration in text order: left dependents, parent, right dependents.
    def textorder (self): return textorder(self)

    ##  List of nodes (pre-order).
    def nodes (self): return nodes(self)

    ##  Iteration over nodes (pre-order).
    def iter_nodes (self): return iter_nodes(self)

    ##  List of edges.
    def edges (self): return edges(self)

    ##  Iteration over edges.
    def iter_edges (self): return iter_edges(self)

    ##  List of subtrees.
    def subtrees (self, which): return subtrees(self, which)

    ##  Iteration over subtrees.
    def iter_subtrees (self, which): return iter_subtrees(self, which)

    ##  The first subtree with the given category.
    def subtree (self, which): return subtree(self, which)

    ##  Iteration over paths from root to leaf.
    def paths (self): return paths(self)

    ##  Iteration over leaves.
    def leaves (self): return leaves(self)

    ##  Iteration over words.
    def words (self): return words(self)

    ##  Iteration over (cat, word) pairs.
    def tagged_words (self): return tagged_words(self)

    ##  Words joined with spaces.
    def terminal_string (self): return terminal_string(self)

    ##  True if the tree has no words.
    def is_empty (self): return is_empty(self)

    ##  True if there are no empty leaves.
    def is_efree_tree (self): return is_efree_tree(self)

    ##  True if there are no unary nodes.
    def is_unaryfree_tree (self): return is_unaryfree_tree(self)

    ##  Deep copy.
    def copy_tree (self): return copy_tree(self)

    ##  Delete nodes with the given categories.
    def delete_nodes (self, cats): return delete_nodes(self, cats)

    ##  Eliminate empty nodes.
    def eliminate_epsilons (self, headrules=None): return eliminate_epsilons(self, headrules)

    ##  Set parent values throughout the tree.  (Destructive.)
    def set_parents (self, parent=None): return set_parents(self, parent=None)

    ##  Chases parent links.
    def getroot (self): return getroot(self)


#--  Node accessors  -----------------------------------------------------------

##  Get the value of the 'cat' attribute, if there is one.

def getcat (node):
    if hasattr(node, 'cat'): return node.cat

##  Get the value of the 'children' attribute, if there is one.

def getchildren (node):
    if hasattr(node, 'children'): return node.children

##  Get the value of the 'parent' attribute, if there is one.

def getparent (node):
    if hasattr(node, 'parent'): return node.parent

##  Get the value of the 'word' attribute, if there is one.

def getword (node):
    if hasattr(node, 'word'): return node.word
    elif isinstance(node, str): return node

##  Get the value of the 'nld' attribute, if there is one.

def getnld (node):
    if hasattr(node, 'nld'): return node.nld

##  Get the value of the 'role' attribute, if there is one.

def getrole (node):
    if hasattr(node, 'role'): return node.role

##  Get the value of the 'id' attribute, if there is one.

def getid (node):
    if hasattr(node, 'id'): return node.id

##  Get the value of the 'sem' attribute, if there is one.

def getsem (node):
    if hasattr(node, 'sem'): return node.sem


#--  Node predicates  ----------------------------------------------------------

##  Node type for leaves.
LeafType = 'leaf'

##  Node type for unheaded phrases.
UnheadedPhraseType = 'unheaded phrase'

##  Node type for headed phrases.
HeadedPhraseType = 'headed phrase'

##  Node type for governors.
GovernorType = 'governor'

##  Returns true if children are boolean true.

def is_interior (node):
    return bool(getchildren(node))

##  A leaf node is one whose children are boolean false.

def is_leaf (node):
    return bool(node) and not getchildren(node)

##  A governor has both children and a word.

def is_governor (node):
    return bool(getchildren(node)) and bool(getword(node))

##  A phrase has children but no word.

def is_phrase (node):
    return bool(getchildren(node)) and not getword(node)

##  A headed phrase is a phrase and has a head child.

def is_headed_phrase (node):
    return is_phrase(node) and bool(head_child(node))

##  An unheaded phrase is a phrase and has no head child.

def is_unheaded_phrase (node):
    return is_phrase(node) and not head_child(node)

##  A leaf word is a leaf that has a word.

def is_leaf_word (node):
    return is_leaf(node) and bool(getword(node))

##  An empty leaf is a leaf that has no word.

def is_empty_leaf (node):
    return is_leaf(node) and not getword(node)

##  A unary node is a phrase that has exactly one child.

def is_unary (node):
    return is_phrase(node) and len(node.children) == 1

##  Node type is one of: LeafType, GovernorType, HeadedPhraseType, or UnheadedPhraseType.

def nodetype (node):
    if is_leaf(node): return LeafType
    elif getword(node): return GovernorType
    elif head_child(node): return HeadedPhraseType
    else: return UnheadedPhraseType


#--  Node structural access  ---------------------------------------------------

##  Returns the (first) child that has role 'head', if any.

def head_child (node):
    children = getchildren(node)
    if children:
        for c in children:
            if getrole(c) == 'head':
                return c
    return None

##  Returns the index of the (first) child that has role 'head', or -1.

def head_index (node):
    children = getchildren(node)
    if children:
        for i,c in enumerate(children):
            if getrole(c) == 'head':
                return i
    return -1

##  Returns the index of the child, or -1 if it is not among the children.

def child_index (node, child):
    children = getchildren(node)
    if children:
        for i,c in enumerate(node.children):
            if c == child:
                return i
    return -1

##  If a node has a word, nld splits left and right dependents.
#   Otherwise, the head child separates left and right dependents.

def left_dependents (node):
    if is_leaf(node): return []
    children = getchildren(node)
    if getword(node):
        j = getnld(node)
        if j is None: j = len(children)
    else:
        j = head_index(node)
        if j < 0: j = len(children)
    return children[:j]

##  See left_dependents().

def right_dependents (node):
    if is_leaf(node): return []
    children = getchildren(node)
    if getword(node):
        i = getnld(node)
        if i is None: i = len(children)
    else:
        i = head_index(node) + 1
        if i == 0: i = len(children)
    return children[i:]

##  A tuple consisting of the category and each of the child categories,
#   but None if the node has no children.

def expansion (node):
    children = getchildren(node)
    if children:
        return tuple([getcat(node)] + [getcat(child) for child in children])


#--  Node destructive  ---------------------------------------------------------

##  Delete the i-th child.  Adjusts nld if necessary.  Destructive.

def delete_child (node, i):
    del node.children[i]
    if node.nld and i < node.nld:
        node.nld -= 1


#--  Tree types  ---------------------------------------------------------------

##  True just in case every node is either a leaf or a headed phrase.

def is_headed_tree (tree):
    return all((is_headed_phrase(node) or is_leaf(node)) for node in nodes(tree))

##  True if every node is an unheaded phrase or leaf.

def is_unheaded_tree (tree):
    return all((is_unheaded_phrase(node) or is_leaf(node)) for node in nodes(tree))

##  True if every node is a governor or leaf.

def is_dependency_tree (tree):
    return all((is_governor(node) or is_leaf(node)) for node in nodes(tree))

##  LeafType if the tree is a single node, t if all nodes are either leaves or have
#   type t, and None otherwise.

def treetype (node):
    if not node.children: return LeafType
    else: return __all_nodetypes(node, nodetype(node))

def __all_nodetypes (node, t):
    if t != None:
        for child in node.children:
            childtype = nodetype(child)
            if childtype == None or (childtype != LeafType and childtype != t):
                return None
    return t


#--  Load and parse  -----------------------------------------------------------

##  Load from file.  Example of input:
#
#       (S
#          (NP:subj foo [1]
#             (Det the)
#             (N dog))
#          (VP:head [2]
#             (V chased)
#             (NP:dobj
#                (Det the)
#                (N cat))))

def load_trees (fn):
    return list(iter_trees(fn))

##  Convert a string to trees.

def parse_trees (s):
    return list(iter_trees(StringIO(s)))

##  Convert a string to one tree.

def parse_tree (s):
    trees = parse_trees(s)
    if len(trees) != 1:
        raise Exception("Not a unique tree")
    return trees[0]

##  Syntax for a file containing trees.
TreeSyntax = Syntax('():&')

##  Iterate over trees from the file.

def iter_trees (filename):
    try:
        infile = iter_tokens(filename, syntax=TreeSyntax)
        while True:
            yield __scan_tree(infile)
    except StopIteration:
        pass

def __scan_tree (infile):
        if infile.has_next('eof'): raise StopIteration
        cat = role = word = id = nld = children = None

        infile.require('(')

        ## may be missing, then cat is None
        cat = infile.accept('word')
        
        ## role?
        if infile.accept(':'):
            role = infile.require('word')

        ## id?
        if infile.accept('&'):
            id = infile.require('word')

        ## children
        children = []
        while not infile.accept(')'):

            ## word?
            if infile.has_next('word'):
                if word != None: infile.error("Multiple words for node")
                word = next(infile)
                nld = len(children)

            else:
                children.append(__scan_tree(infile))

        if not children:
            children = None
            nld = None

        return Tree(cat=cat, children=children, word=word, nld=nld, role=role, id=id)


#--  Print and save  -----------------------------------------------------------

##  Print a tree.

def print_tree (tree, numerate=True, getfeatures=None):
    print(tree_string(tree, numerate, getfeatures))

##  Convert a tree to a string for printing.

def tree_string (tree, numerate=True, getfeatures=None):
    (idx, x, last, width) = __pp_tree(tree, 0, 0, getfeatures)
    return __pp_string(x, width + 4, numerate)

def __pp_string (x, width, numerate):
    (index, indent, string, sem, children) = x
    if index is None:
        if numerate: s = '     '
        else: s = ' '
        s += (' ' * indent)
        s += string
        return s
    else:
        if numerate: s = '%-4d' % index
        else: s = ''
        s += (' ' * indent)
        s += '('
        s += string
        if sem is not None:
            if not isinstance(sem, str): sem = repr(sem)
            s += (' ' * (width - len(string)))
            s += ' : '
            s += sem
        if children:
            return '\n'.join([s] + [__pp_string(c, width, numerate)
                                    for c in children])
        else:
            return s

def __pp_word (word):
    if not isinstance(word, str): word = str(word)
    return TreeSyntax.scanable_string(word)

def __pp_tree (tree, idx, indent, getfeatures):
    myindex = idx
    myindent = indent
    mystring = ''

    idx += 1
    indent += 3
	
    cat = getcat(tree)
    if cat: mystring += __pp_word(cat)

    role = getrole(tree)
    if role: mystring += ":" + __pp_word(role)

    word = getword(tree)
    nld = getnld(tree)
    mywidth = 0
    if nld is not None:
        hstring = __pp_word(word)
        head = [None, indent, hstring, None, None]
        mywidth = len(hstring)
    elif word:
        mystring += " " + __pp_word(word)

    id = getid(tree)
    if id is not None: mystring += " &" + __pp_word(id)

    if getfeatures:
        anno = getfeatures(tree)
    else:
        anno = getsem(tree)

    me = [myindex, myindent, mystring, anno, None]
    last = me

    children = getchildren(tree)
    if children:
        mychildren = []
        for i in range(0, len(children)):
            if i == nld: mychildren.append(head)
            (idx, child, last, w) = __pp_tree(children[i], idx, indent, getfeatures)
            mychildren.append(child)
            if w > mywidth: mywidth = w
        if nld == len(children):
            mychildren.append(head)
            last = head
        me[4] = mychildren

    last[2] += ')'
    w = len(me[2])
    if w > mywidth: mywidth = w

    return (idx, me, last, mywidth)

##  Save trees to file.

def save_trees (trees, filename=None):
    f = outfile(filename)
    for tree in trees:
        f.write(tree_string(tree, numerate=False))
        f.write('\n')
    return close(f)


#--  Tabular tree files  -------------------------------------------------------

##  Load trees from a tabular-format file.

def load_tabular_trees (filename=None, morefields=None):
    return list(iter_tabular_trees(filename, morefields))

##  Iterate over trees in a tabular-format file.

def iter_tabular_trees (filename=None, morefields=None):
    f = iter_records(filename)
    tree_count = 0
    try:
        while True:
            tree = __read_tabular_tree(f, morefields)
            if tree is None: raise Exception("Unexpected ']'")
            tree.provenance = (filename, tree_count)
            tree_count += 1
            yield tree
    except StopIteration:
        pass

def __read_tabular_tree (f, morefields):
    fields = next(f)
    if fields[0] == "]": return None

    node = Tree()
    n = len(fields)

    if n > 1 and fields[1]:
        node.cat = fields[1]

    if n > 2 and fields[2]:
        node.word = fields[2]

    if n > 3 and fields[3]:
        node.role = fields[3]

    if n > 4 and fields[4]:
        node.nld = int(fields[4])

    if n > 5 and fields[5]:
        node.id = fields[5]

    if morefields:
        morefields(node, fields)

    if fields[0] == "[":
        node.children = []
        while True:
            child = __read_tabular_tree(f, morefields)
            if child is None: break
            node.children.append(child)

    elif fields[0] != "+":
        raise Exception("Bad record: " + str(fields))

    return node

##  Save trees to file in tabular format.

def save_tabular_trees (trees, filename=None):
    return save_records(__iter_treelist_records(trees), filename)

def __iter_treelist_records (trees):
    for tree in trees:
        for record in __iter_tree_records(tree):
            yield record

def __iter_tree_records (tree):
    cat = getcat(tree)
    if cat: cat = str(cat)
    else: cat = ''

    word = getword(tree)
    if word: word = str(word)
    else: word = ''

    role = getrole(tree)
    if role: role = str(role)
    else: role = ''

    nld = getnld(tree)
    if nld is not None: nld = str(nld)
    else: nld = ''
	
    id = getid(tree)
    if id: id = str(id)
    else: id = ''

    children = getchildren(tree)
    if children:
        yield ['[', cat, word, role, nld, id]
        for child in children:
            for record in __iter_tree_records(child):
                yield record
        yield [']']
    else:
        yield ['+', cat, word, role, nld, id]


#--  Draw tree  ----------------------------------------------------------------

##  Convert a tree to dot commands.

def tree_to_dot (tree, filename=None):
    out = outfile(filename)
    out.write("digraph {\n")
    out.write("    node [shape=box];\n")
    out.write("    edge [arrowhead=none];\n")
    __dot1(tree, 0, 1, out)
    out.write("}\n")
    out.close()

def __dot1 (node, parent_id, id, out):
    "For use by L{Tree.dot()}.  Return value is last id allocated."
	
    ##  The label is the category, plus the word if it exists
    if node.cat: label = str(node.cat)
    else: label = ""
    if node.word: label += "\\n" + node.word
	    
    out.write("    n" + str(id) + " [label=\"" + label + "\"];\n")

    ##  Write the incoming link, unless this is the root
    if parent_id > 0: out.write("    n" + str(parent_id) + " -> n" + str(id) + ";\n")
	
    ##  Terminal node
    if not node.children: return id

    ##  Nonterminal node
    else:
        child_id = id
        for child in node.children:
            child_id = __dot1(child, id, child_id + 1, out)
        return child_id

##  Draw a tree.  Invokes dot.

def draw_tree (tree, fn=None):
    if fn:
        __draw1(tree, fn)
    else:
        fn = tmpfile()
        __draw1(tree, fn)
        os.system('open %s.pdf' % fn)

def __draw1 (tree, fn):
    dotfn = fn + ".dot"
    ps = fn + ".ps"
    pdf = fn + ".pdf"
    dot(tree, dotfn)
    os.system('/cl/bin/dot -Tps2 %s -o %s' % (dotfn, ps))
    os.system('pstopdf %s -o %s' % (ps, pdf))


#--  Walks  --------------------------------------------------------------------

##  Do a pre-order walk of a tree.

def preorder (node):
    stack = [node]
    while stack:
        node = stack.pop()
        children = getchildren(node)
        if children:
            stack.extend(reversed(children))
        yield node

##  Do a text-order walk of a tree.

def textorder (node):
    stack = [node]
    expanded = None
    while stack:
        node = stack.pop()
        if node == expanded:
            yield stack.pop()
        else:
            children = getchildren(node)
            if children:
                h = getnld(node)
                if h is None: h = 0
                stack.extend(reversed(children[h:]))
                stack.append(node)
                stack.append(expanded)
                stack.extend(reversed(children[:h]))
            else:
                yield node


#--  Nodes and edges  ----------------------------------------------------------

##  Returns a list of nodes.

def nodes (tree):
    return list(iter_nodes(tree))
    
##  Iterates over nodes in pre-order.  Note that the words will not necessarily
#   be in the right order.

def iter_nodes (tree):
    return preorder(tree)

##  List of edges.

def edges (tree):
    return list(iter_edges(tree))

##  An iterator over the edges (node,child) in the subtree rooted at this node.

def iter_edges (tree):
    for node in preorder(tree):
            if node.children:
                for child in node.children:
                    yield (node, child)


#--  Subtrees  -----------------------------------------------------------------

##  List of subtrees whose category is given.

def subtrees (tree, which):
    return list(iter_subtrees(tree, which))

##  Iterate over subtrees that have the given category.

def iter_subtrees (tree, which):
    if isinstance(which, str):
        f = lambda x: getcat(x) == which
    else:
        f = which
    return __subtrees1(tree, f)

def __subtrees1 (tree, f):
    if f(tree): yield tree
    else:
        children = getchildren(tree)
        if children:
            for c in children:
                for node in __subtrees1(c, f):
                    yield node

##  Returns a single subtree.  Error if it is not unique.

def subtree (tree, which):
    ts = subtrees(tree, which)
    if len(ts) != 1: raise Exception("Not unique")
    return ts[0]


#--  Paths and leaves  ---------------------------------------------------------

##  Returns the category sequences from root to leaf in the tree.

def paths (tree):
    return ['/'.join(path) for path in __paths1(tree)]

def __paths1 (tree):
    if tree.children:
        return [[tree.cat] + path for child in tree.children for path in __paths1(child)]
    else:
        return [[tree.cat]]

##  Returns the yield as a list of nodes.  Includes empty leaves.

def leaves (tree):
    return [node for node in nodes(tree) if is_leaf(node)]

##  Like the yield, but it is a list of words (strings).

def words (tree):
    return [node.word for node in textorder(tree) if node.word]

##  Returns pairs (word,cat) for the word nodes of the tree.

def tagged_words (tree):
    return [(node.word, node.cat) for node in textorder(tree) if node.word]

##  Returns the yield as a string.

def terminal_string (tree):
    return " ".join(words(tree))


#--  Predicates  ---------------------------------------------------------------

##  Returns true if the yield is the empty string.

def is_empty (node):
    if node.word: return False
    elif not node.children: return True
    else:
        for child in node.children:
            if not is_empty(child): return False
        return True

##  Whether every node has either children or a word.

def is_efree_tree (tree):
    return all((node.children or node.word) for node in tree.nodes())

##  True if no node is unary.

def is_unaryfree_tree (tree):
    return all((not is_unary(node)) for node in tree.nodes())


#--  Copy  ---------------------------------------------------------------------

##  Deep copy.

def copy_tree (tree):
    if tree.children:
        children = [copy_tree(child) for child in tree.children]
    else:
        children = None
    return tree.copy(children=children)


#--  Delete nodes  -------------------------------------------------------------

##  Delete any node (except the root node) whose cat is in cats.
#   Destructive.

def delete_nodes (tree, cats):
    i = 0
    while i < len(tree.children):
        child = tree.children[i]
        if child.cat in cats:
            delete_child(tree, i)
        else:
            delete_nodes(child, cats)
            i += 1


#--  Epsilon elimination  ------------------------------------------------------

##  Make sure every node has either a word or children.
#   Node.nld will be updated, but there is no guarantee that heads
#   will be preserved.

def eliminate_epsilons (node, headrules=None):
    __eliminate_epsilons1(node, headrules)


def __eliminate_epsilons1 (node, headrules):

    if not node.nld is None:
        lds = __eliminate_epsilons2(left_dependents(node), headrules)
        rds = __eliminate_epsilons2(right_dependents(node), headrules)
        node.children = lds + rds
        node.nld = len(lds)

    elif node.children:
        node.children = __eliminate_epsilons2(node.children, headrules)

    if node.children or node.word: return node
    else: return None


def __eliminate_epsilons2 (children, headrules):
    return [_f for _f in (__eliminate_epsilons1(child, headrules) for child in children) if _f]


#--  Set parents  --------------------------------------------------------------

##  Set the parent attribute of every node.  Destructive.

def set_parents (tree, parent=None):
    tree.parent = parent
    if tree.children:
        for c in tree.children:
            set_parents(c, tree)

##  Trace parent links up to the root.

def getroot (node):
    while node.parent:
        node = node.parent
    return node


#--  TreeBuilder  --------------------------------------------------------------

##  Tool for building a tree top-down.

class TreeBuilder:

    ##  Constructor.

    def __init__ (self):

        ##  Stack of incomplete nodes.
        self.stack = []

        ##  Roots.
        self.roots = []

    ##  If there is a parent, add the node as child

    def __add_child (self, node):
        if len(self.stack) > 0:
            parent = self.stack[-1]
            if parent.children == None: raise Exception("Leaf node cannot be parent")
            if hasattr(node, 'parent'): raise Exception('Child already has parent')
            parent.children.append(node)
            node.parent = parent

    ##  Start a tree.

    def start (self, cat, word=None, role=None, id=None):
        node = Tree(cat=cat, children=[], word=word, role=role, id=id)
        self.__add_child(node)
        self.stack.append(node)
        return node

    ##  This is used to mark the position where a governor occurs among its dependents.

    def middle (self):
        if not self.stack: raise Exception("Head, but no parent")
        parent = self.stack[-1]
        if parent.nld != None: raise Exception("Multiple governor positions specified")
        parent.nld = len(parent.children)

    ##  The current node is complete.

    def end (self):
        node = self.stack.pop()
        if len(self.stack) == 0:
            self.roots.append(node)
            if hasattr(node, 'parent'): raise Exception('Root has parent')
            node.parent = None
        return node

    ##  Add a leaf child.

    def leaf (self, cat, word, role=None, id=None):
        node = Tree(cat=cat, word=word, role=role, id=id)
        self.__add_child(node)
        return node

    ##  Return the roots, but only if the stack is empty.

    def trees (self):
        if self.stack: raise Exception("Incomplete tree")
        roots = self.roots
        self.roots = []
        return roots

    ##  Return the sole root.  Error if it is not unique.

    def tree (self):
        if self.stack: raise Exception("Incomplete tree")
        if not self.roots: raise Exception("No trees")
        if len(self.roots) > 1: raise Exception("Multiple trees")
        root = self.roots[0]
        self.roots = []
        return root
