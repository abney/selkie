######################################################################
#                                                                    #
#  Chapter 1                                                         #
#  Generalities                                                      #
#                                                                    #
######################################################################


# 1.1  Getting started  ----------------------------------------------

from nell import *
hello()


# 1.2.1  Iterables  --------------------------------------------------

def pots ():
    for i in range(11):
        yield 2**i

pots()
list(pots())
nth(pots(), 2)

iter = pots()
nth(iter, 2)

list(iter)

head(pots())
tail(pots())
head(pots(), 3)
tail(pots(), 3)

list(islice(pots(), 2, 5))

count(pots())
counts('abracadabra')
