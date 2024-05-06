
Root -> S.-
Root -> :S.- FinalPunct
Root -> NP.*.-
Root -> AdjP
Root -> NP.*.wh Aux.$n.$v NP.$n.- :VP.$v.np
Root -> Aux.$n.$v NP.$n :VP.$v.-
Root -> VP.base.-
Root -> PP.*
Root -> Date

SC.$c.$g -> :C.$c S.$g
SC.inf.$g -> :P.to VP.base.$g

RC -> :RPron.$n VP.$n.-
RC -> :RPron S.np

S.$g -> NP.$n.- :VP.$n.$g
S.$g -> NP.$n.- Comma :VP.$n.$g

VP.$f.$g -> :VP.$f.$g Date

VP.$f.-  -> :VC.$f.i.-
VP.$f.-  -> :VC.$f.t.-  NP.*.-
VP.$f.np -> :VC.$f.t.-
VP.$f.-  -> :VC.$f.t.$p NP.*.- PP.$p
VP.$f.np -> :VC.$f.t.$p        PP.$p
VP.$f.-  -> :VC.$f.t.np NP.*.- NP.*.-
VP.$f.np -> :VC.$f.t.np NP.*.-
VP.$f.-  -> :VC.$f.i.np        NP.*.-
VP.$f.-  -> :VC.$f.i.$p        PP.$p
VP.$f.-  -> :VC.$f.i.adj       AdjP
VP.$f.-  -> :VC.$f.t.$c NP.*.- SC.$c
VP.$f.np -> :VC.$f.t.$c        SC.$c
VP.$f.-  -> :VC.$f.i.$c        SC.$c

VC.$f.$t.$c -> Aux.$f.$v :VC.$v.$t.$c
VC.$f.$t.$c -> V.$f.$t.$c

PP.$p -> :P.$p NP.*.-

NP.$n.$w -> :Pron.$n.$w
NP.$n.- -> :Name.$n
NP.$n.$w -> Det.$n.$w :N2.$n
NP.$n.- -> :N2.$n
NP.pl.- -> :NP Conj NP
NP.$n.- -> :Name.$n.- Comma PredP
NP.$n.- -> :NP.$n.- Comma Name.$n.-

PredP -> :AdjP
PredP -> :NP.sg
PredP -> :AdjP And AdjP
PredP -> :AdjP And NP.sg
PredP -> :NP.sg And AdjP
PredP -> :NP.sg And NP.sg

Name.sg -> Title :PersonName
Name.sg -> :PersonName
PersonName -> :FName
PersonName -> :LName
PersonName -> FName :LName
PersonName -> Initials :LName
PersonName -> FName Initials :LName
Name.sg -> :UnknownNames

UnknownNames -> UnknownName :UnknownNames
UnknownNames -> Initials :UnknownNames
UnknownNames -> Acronym :UnknownNames
UnknownNames -> :UnknownName
UnknownNames -> :Initials
UnknownNames -> :Acronym

N2.$n -> :N2.$n RC
N2.$n -> :N1.$n

N1.$n -> Adj1 :N1.$n
N1.$n -> :N0.$n.-
N0.$n -> N.sg.- :N0.$n
N0.$n -> :N.$n.-
N0.$n -> :N.$n.$p PP.$p

AdjP -> :Adj1.-
AdjP -> :Adj1.$p PP.$p

Adj1.$p -> Deg :Adj.$p
Adj1.$p -> MeasP :Adj.$p
Adj1.$p -> :Adj.$p

MeasP -> Num :Unit

Date -> :Month Day
