######################################################################
#                                                                    #
#  Chapter 3                                                         #
#  Finite-state automata                                             #
#                                                                    #
######################################################################

from nell import *


# 3.1  Basics  -------------------------------------------------------

a = dfsa()
a.edge('1', '2', 'the')
a.edge('2', '2', 'big')
a.edge('2', '2', 'red')
a.edge('2', '3', 'dog')
a.final_state('3')
a.dump()

a['1']['the']
a['2']['dog']
a['2']['the']

a['1']

a['3'].is_final

def accepts (self, input):
    q = self.start
    for sym in input:
        q = q[sym]
        if q == None: return False
    return q.is_final

accepts(a, ['the', 'dog'])
accepts(a, ['the', 'cat'])
accepts(a, ['the', 'red', 'big', 'red', 'dog'])
accepts(a, ['the'])

a.accepts(['the', 'dog'])
a.accepts(['the', 'cat'])
a.accepts(['the', 'red', 'big', 'red', 'dog'])
a.accepts(['the'])


# 3.2  Fsa file format  ----------------------------------------------

cat(ex.fsa1)

a = dfsa(ex.fsa1)
a.dump()


# 3.3  More about states  --------------------------------------------

a['3']

a.states
q = a.states[2]
q
q.name
q.index

a['5']
a['2']
a[2]

a.state('6')
a.state('hi')
a.state(2)
a.state(frozenset([1,2,4]))
a.states

a.rename_states()
a.states
a.states[0].name
a.states[0].index


# 3.4  Nondeterministic automata  ------------------------------------

a = nfsa(ex.fsa1)
a.edge('2', '3', 'red')
a.dump()

a.edge('1', '2')
a.dump()

d = dfsa(ex.fsa1)
d.edge('2', '3', 'red')
d.edge('1', '2')

a['2']['red']
a['2']['big']
a['1']['']
a['1']['dog']

d = dfsa(a)
d.dump()
d.accepts(['red'])
d.accepts(['red', 'dog'])
d.accepts(['dog', 'red'])
