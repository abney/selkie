######################################################################
#                                                                    #
#  Chapter 5                                                         #
#  Trees                                                             #
#                                                                    #
######################################################################

from nell import *


# 5.1.  Overview  ----------------------------------------------------

n1 = Node('Det')
n2 = Node('N')
n3 = Node('NP', [n1, n2])
n3.cat()
n3.children()
n3.isleaf()
n1.isleaf()
n1.children()

n3.dump()

print(n3)

n3[2]


n4 = Node('NP', [Node('Det', [Node('the')]),
                 Node('N', [Node('dog')])])
print(n4)

n5 = Node('NP', [Node('Det', word='the'), Node('N', word='dog')])
print(n5)
n5[1].dump()

t = tree('(NP (Det the) (N cat))')
print(t)

cat(ex.t1)

trees = list(treefile(ex.t1))
t = trees[0]
print(t)

n5.write('/tmp/foo')
cat('/tmp/foo')
rm('/tmp/foo')

p = tree('''
    (S (NP (Det the) (N dog))
       (VP (V barked))
       (Adv loudly))
''')
print(p)

h = tree('''
    (S (NP (Det the) <H> (N dog))
       <H>
       (VP <H> (V barked))
       (Adv loudly))
''')
print(h)

h
h.head()
h.head_child()

d = tree('(V barked (N dog (Det the) <G>) <G> (Adv loudly))')
print(d)

d.head_child()
d.left_dependents()
d.right_dependents()

h.head_child()
h.left_dependents()
h.right_dependents()

p.sentence()
h.sentence()
d.sentence()

t = tree('(S (N dog (Det the) <G>) <H> (V barked))')
print(t)

print(headed(p))

print(dependency(h))
print(dependency(p))

e = tree('''
  (S
    (NP (N ))
    (VP
      (VBZ )
      (RB surely)
      (NP Fido)))
''')
print(efree(e))
print(headed(e))
print(efree(headed(e)))
print(headed(efree(e)))
print(dependency(e))
print(efree(dependency(e)))
print(dependency(efree(e)))

print(d)
s = stemma(d)
print(s)
len(s)
s[2]
s.root_index()

s[4]

tb = TreeBuilder()
tb.start('S')
tb.start('NP', role='subj')
tb.leaf('Det', 'the')
tb.leaf('N', 'dog')
tb.end()
tb.start('VP', ishead=True)
tb.leaf('V', 'chased')
tb.start('NP', role='dobj')
tb.leaf('Det', 'the')
tb.leaf('N', 'cat')
tb.end()
tb.end()
tb.end()
trees = tb.done()
print(trees[0])

t = tree('''
    (NP:subj foo [1]
        (Det the)
        <H>
        (N dog))
    ''')
t.role()
t.word()
t.id()
t.head()
t.children()

tree1 = next(PrettyTreeFile(ex.tree1))
print(tree1)

tree1.write()

tree1.write('/tmp/foo.tab')
cat('/tmp/foo.tab')
rm('/tmp/foo.tab')
