##  @package seal.ml.prob
#   Functions related to probabilities.

from math import log, exp
import random


#--  Functions  ----------------------------------------------------------------

##  The natural log of 2.
LOG2 = log(2)

##  Log base two.

def lg (x):
    return log(x) / LOG2

##  The entropy of a distribution.

def entropy (dist):
    total = 0.0
    for p in dist:
        if p != 0:
            total += p * lg(p)
    return -total

##  Dot product of two vectors.

def dotprod (v1, v2):
    n = len(v1)
    if len(v2) != n: raise Exception("Vector lengths differ")
    total = 0.0
    for i in range(n):
        total += v1[i] * v2[i]
    return total

##  Cross entropy of p with q.

def cross_entropy (p, q):
    n = len(p)
    if len(q) != n: raise Exception("Vector lengths differ")
    total = 0.0
    for i in range(n):
        if p[i] != 0:
            total += p[i] * lg(q[i])
    return -total

##  Divergence of p from q.

def divergence (p, q):
    return cross_entropy(p, q) - entropy(p)

##  F-measure given precision and recall.

def f_measure (p, r):
    return 2*p*r/(p+r)


#--  Dist  ---------------------------------------------------------------------

##  A probability distribution.

class Dist (object):

    ##  Constructor.

    def __init__ (self, items=None, dim=None, cdim=0):

        ##  The dimensions of the key.
        self.dim = dim

        ##  An item has an extra elt for the value.
        self.cdim = cdim

        ##  Contents.
        self.contents = dict()

        if items:
            for item in items:
                self.add(item)

    ##  Add an item.

    def add (self, item):
        if self.dim is None:
            self.dim = len(item) - 1
        elif len(item) != self.dim + 1:
            raise KeyError("Wrong dimensionality for key")

        key = item[0]
        if self.dim == 1:
            value = item[1]
            self.contents[key] = value
        else:
            item = item[1:]
            if key in self.contents:
                sd = self.contents[key]
            else:
                cdim = self.cdim - 1
                if cdim < 0: cdim = 0
                sd = Dist(dim=self.dim - 1, cdim=cdim)
                self.contents[key] = sd
            sd.add(item)

    ##  Get the count for an item.

    def __getitem__ (self, key):
        if isinstance(key, tuple):
            key0 = key[0]
            if len(key) > 1:
                key_rest = key[1:]
            else:
                key_rest = None
        else:
            key0 = key
            key_rest = None
        if key0 in self.contents:
            v = self.contents[key0]
            if key_rest:
                return v[key_rest]
            else:
                return v
        else:
            return 0

    ##  Conditions.

    def conds (self):
        return list(self.iterconds())

    ##  Iteration over conditions.

    def iterconds (self):
        if self.cdim <= 0:
            pass
        elif self.cdim == 1:
            for k in self.contents.keys():
                yield k
        else:
            for k0 in self.contents.keys():
                for krest in self.contents[k0].iterconds():
                    yield (k0,) + krest

    ##  Items.

    def items (self):
        return list(self.items())

    ##  Iteration over items.

    def iteritems (self):
        if self.dim == 1:
            for k,v in self.contents.items():
                yield (k,v)
        else:
            for k,sd in self.contents.items():
                for item in sd.items():
                    yield (k,) + item
