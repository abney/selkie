S -> NP.$n VP.$n       : (!qs ($2 $1))
NP.sg -> Name          : $1
NP.$n -> Det.$n N.$n   : (!q $1 @ ($2 @))
VP.$f -> V.$f.i.0      : $1
VP.$f -> V.$f.t.0 NP.* : (lambda @ ($1 @ $2))
