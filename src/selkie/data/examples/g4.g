# a tiny feature grammar

S -> NP.$n VP.$n
NP.$n -> Det.$n N.$n
VP.$n -> V.$n.i.-
VP.$n -> V.$n.t.- NP
VP.$n -> V.$n.i.$p PP.$p
VP.$n -> V.$n.t.$p NP PP.$p
PP.$p -> P.$p NP
