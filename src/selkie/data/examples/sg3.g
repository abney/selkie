
features {
    auxsel { pred ing en enp base }
    cjform { and or }
    vform { base en enp ing pl sg 1s }
    vsel { np to if that pred ing enp 0 }
    trans { i t }
    num { sg pl 1s obj }
    pform { for in loc }
    mform { by to of }
    cform { if that }
    gap { + - }
}

categories {
    Start Root Greeting YN WhInv Inf RC RS PVR
    AdjP Adj Adv Deg Unit
    IndefArt Name
    Wh WhAdv WhDet RelPron
    VP.vform.gap
    Aux.vform.auxsel V.vform.trans.vsel
    NP.num Pron.num QPron Det.num PNom.num Q.num N2.num N1.num N.num Num.num
    WhNP.num WhPron.num
    PP.pform P.pform MP.mform M.mform SC.cform.gap C.cform
    Preconj.cjform Conj.cjform
    S.gap
}

Start -> Root : $1
Start -> NP.* : $1
Start -> PP.* : $1
Start -> Greeting : ($1)

# Clauses
Root -> S.-               : $1
Root -> YN                : (yn $1)
Root -> WhInv             : (wh @ (!g= @ $1))
Root -> Wh                : (wh @ (!g= @ $1))

YN -> Aux.$n.$v NP.$n VP.$v.-            : (!qs ($3 $2))
YN -> Aux.$n.pred NP.$n AdjP             : (!qs ($3 $2))
YN -> Aux.$n.pred NP.$n PNom.*           : (!qs ($3 $2))
WhInv -> WhNP.* Aux.$n.$v NP.$n VP.$v.+  : (!qs ($4 $3))
Wh -> WhNP.$n VP.$n.-                    : (!qs ($2 $g))
Wh -> WhNP.* Aux.$n.pred AdjP            : (!qs ($3 $g))
Wh -> WhNP.* Aux.$n.pred PNom.*          : (!qs ($3 $g))

RC -> RS                             : (lambda @ (!g= @ $1))
RS -> RelPron VP.$n.-                : (!qs ($2 $g))
RC -> RelPron S.+                     : (lambda @ (!g= @ $2))

S.$g -> NP.$n VP.$n.$g                  : (!qs ($2 $1))
S.- -> S.- Conj.* S.-                   : ($2 $1 $3)
S.- -> Preconj.$t S.- Conj.$t S.-       : ($3 $2 $4)

# Verb complements
VP.$f.- -> V.$f.i.0            : $1
VP.$f.- -> V.$f.t.0 NP.*       : (lambda @ ($1 @ $2))
VP.$f.+ -> V.$f.t.0            : (lambda @ ($1 @ $g))
VP.$f.- -> V.$f.t.np NP.* NP.* : (lambda @ ($1 @ $3 $2))
VP.$f.+ -> V.$f.t.np NP.*      : (lambda @ ($1 @ $g $2))
VP.$f.- -> V.$f.i.$p PP.$p     : (lambda @ ($1 @ $2))
VP.$f.- -> V.$f.t.$p NP.* MP.$p : (lambda @ ($1 @ $2 $3))
VP.$f.+ -> V.$f.t.$p MP.$p      : (lambda @ ($1 @ $g $2))
VP.enp.- -> V.enp.t.0 MP.by     : (lambda @ ($1 $2 @))
VP.enp.- -> V.enp.t.0           : (lambda @ ($1 (!q exists @2 (person @2)) @))
VP.$f.$g -> V.$f.i.$c SC.$c.$g  : (lambda @ ($1 @ (^ $2)))
VP.$f.$g -> V.$f.t.$c NP.* SC.$c.$g : (lambda @ ($1 @ (^ $3) $2))

VP.$f.$g -> Aux.$f.$v VP.$v.$g   : $2
VP.$f.- -> Aux.$f.pred AdjP      : $2
VP.$f.- -> Aux.$f.pred PNom.*    : $2

VP.$f.$g -> Aux.$f.$v PVR VP.$v.$g   : (lambda @ ($2 ($3 @)))
VP.$f.- -> Aux.$f.pred PVR AdjP      : (lambda @ ($2 ($3 @)))
VP.$f.- -> Aux.$f.pred PVR PNom.*    : (lambda @ ($2 ($3 @)))

# Adjuncts
#VP.$f -> VP.$f PP.*      : (mod $1 $2)
#VP.$f -> VP.$f AdvP      : (mod $1 $2)
#VP.$f -> VP.$f SC.*.*    : (mod $1 $2)

# NP
NP.sg -> Name           : $1
NP.$n -> Pron.$n        : $1
NP.sg -> QPron          : (!q $1 @)
NP.$n -> Det.$n Q.$n N2.$n : (!q $1 @ (and ($2 @) ($3 @)))
NP.$n -> Det.$n N2.$n      : (!q $1 @ ($2 @))
NP.pl -> Q.pl N2.pl        : (!q $1 @ ($2 @))
#NP.$n -> Det.$n Q.$n       : (!q $1 @ ($2 @))
NP.pl -> N2.pl             : (!q every @ ($1 @))
N2.$n -> N2.$n PP.loc      : (lambda @ (and ($1 @) ($2 @)))
N2.$n -> N2.$n AdjP        : (lambda @ (and ($1 @) ($2 @)))
N2.$n -> N2.$n RC          : (lambda @ (and ($1 @) ($2 @)))
N2.$n -> N1.$n             : $1
N1.$n -> Adj N1.$n         : (lambda @ (and ($1 @) ($2 @)))
N1.$n -> N.$n MP.of        : (lambda @ ($1 @ $2))
N1.$n -> N.$n              : $1

# PNom
PNom.sg -> IndefArt N2.$n  : $2
PNom.pl -> N2.pl           : $1

# WhNP
WhNP.$n -> WhPron.$n       : $1

# PP
PP.$p -> P.$p NP.*         : (lambda @ ($1 @ $2))
MP.$p -> M.$p NP.*         : $2

# Q
Q.$n -> Num.$n            : $1

# AdjP
AdjP -> Adj               : $1
AdjP -> Deg Adj           : $1
