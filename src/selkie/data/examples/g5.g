Root -> S
Root -> NP
S -> NP.$n VP.$n
NP.$n -> Pron.$n
NP.$n -> Name.$n
NP.$n -> Det.$n Nom.$n
NP.pl -> NP Conj NP
Nom.$n -> Adj1 Nom.$n
Nom.$n -> N.$n
VP.$f -> V.$f.i.-
VP.$f -> V.$f.t.- NP
VP.$f -> V.$f.i.$p    PP.$p
VP.$f -> V.$f.t.$p NP PP.$p
VP.$f -> V.$f.t.np NP NP
VP.$f -> V.$f.i.adj   AdjP
VP.$f -> V.$f.i.$c    SC.$c
VP.$f -> V.$f.t.$c NP SC.$c
PP.$p -> P.$p NP
AdjP -> Adj1.-
AdjP -> Adj1.$p PP.$p
Adj1.$p -> Deg Adj.$p
Adj1.$p -> Adj.$p
SC.$c -> C.$c S
SC.inf -> P.to VP.base
