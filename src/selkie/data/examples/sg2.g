
Start -> Root : $1
Start -> NP[*] : $1
Start -> PP[*] : $1
Start -> Greeting : ($1)

# Clauses
Root -> S[-]              : $1
Root -> YN                : (yn $1)
Root -> WhInv             : (wh @ (!g= @ $1))
Root -> Wh                : (wh @ (!g= @ $1))

YN -> Aux[N,V] NP[N] VP[V,-]            : (!qs ($3 $2))
YN -> Aux[N,pred] NP[N] AdjP             : (!qs ($3 $2))
YN -> Aux[N,pred] NP[N] PNom[*]           : (!qs ($3 $2))
WhInv -> WhNP[*] Aux[N,V] NP[N] VP[V,+]  : (!qs ($4 $3))
Wh -> WhNP[N] VP[N,-]                    : (!qs ($2 $g))
Wh -> WhNP[*] Aux[N,pred] AdjP            : (!qs ($3 $g))
Wh -> WhNP[*] Aux[N,pred] PNom[*]          : (!qs ($3 $g))

RC[*] -> RS                             : (lambda @ (!g= @ $1))
RS -> RelPron VP[*,-]                   : (!qs ($2 $g))
RC[*] -> RelPron S[+]                     : (lambda @ (!g= @ $2))

S[G] -> NP[N] VP[N,G]                  : (!qs ($2 $1))
S[-] -> S[-] Conj[*] S[-]                   : ($2 $1 $3)
S[-] -> Preconj[T] S[-] Conj[T] S[-]       : ($3 $2 $4)

# Verb complements
VP[F,-] -> V[F,i,-]            : $1
VP[F,-] -> V[F,t,-] NP[*]       : (lambda @ ($1 @ $2))
VP[F,+] -> V[F,t,-]            : (lambda @ ($1 @ $g))
VP[F,-] -> V[F,t,np] NP[*] NP[*] : (lambda @ ($1 @ $3 $2))
VP[F,+] -> V[F,t,np] NP[*]      : (lambda @ ($1 @ $g $2))
VP[F,-] -> V[F,i,P] PP[P]     : (lambda @ ($1 @ $2))
VP[F,-] -> V[F,t,P] NP[*] MP[P] : (lambda @ ($1 @ $2 $3))
VP[F,+] -> V[F,t,P] MP[P]      : (lambda @ ($1 @ $g $2))
VP[enp,-] -> V[enp,t,-] MP[by]     : (lambda @ ($1 $2 @))
VP[enp,-] -> V[enp,t,-]           : (lambda @ ($1 (!q exists @2 (person @2)) @))
VP[F,G] -> V[F,i,C] SC[C,G]  : (lambda @ ($1 @ (^ $2)))
VP[F,G] -> V[F,t,C] NP[*] SC[C,G] : (lambda @ ($1 @ (^ $3) $2))

VP[F,G] -> Aux[F,V] VP[V,G]   : $2
VP[F,-] -> Aux[F,pred] AdjP      : $2
VP[F,-] -> Aux[F,pred] PNom[*]    : $2

VP[F,G] -> Aux[F,V] PVR VP[V,G]   : (lambda @ ($2 ($3 @)))
VP[F,-] -> Aux[F,pred] PVR AdjP      : (lambda @ ($2 ($3 @)))
VP[F,-] -> Aux[F,pred] PVR PNom[*]    : (lambda @ ($2 ($3 @)))

# Adjuncts
#VP.$f -> VP.$f PP.*      : (mod $1 $2)
#VP.$f -> VP.$f AdvP      : (mod $1 $2)
#VP.$f -> VP.$f SC.*      : (mod $1 $2)

# NP
NP[sg] -> Name           : $1
NP[N] -> Pron[N]        : $1
NP[sg] -> QPron          : (!q $1 @)
NP[N] -> Det[N] Q[N] N2[N] : (!q $1 @ (and ($2 @) ($3 @)))
NP[N] -> Det[N] N2[N]      : (!q $1 @ ($2 @))
NP[pl] -> Q[pl] N2[pl]        : (!q $1 @ ($2 @))
#NP.$n -> Det.$n Q.$n       : (!q $1 @ ($2 @))
NP[pl] -> N2[pl]             : (!q every @ ($1 @))
N2[N] -> N2[N] PP[loc]      : (lambda @ (and ($1 @) ($2 @)))
N2[N] -> N2[N] AdjP        : (lambda @ (and ($1 @) ($2 @)))
N2[N] -> N2[N] RC[N]       : (lambda @ (and ($1 @) ($2 @)))
N2[N] -> N1[N]             : $1
N1[N] -> Adj N1[N]         : (lambda @ (and ($1 @) ($2 @)))
N1[N] -> N[N] MP[of]        : (lambda @ ($1 @ $2))
N1[N] -> N[N]              : $1

# PNom
PNom[sg] -> IndefArt N2[*]  : $2
PNom[pl] -> N2[pl]           : $1

# WhNP
WhNP[N] -> WhPron[N]       : $1

# PP
PP[P] -> P[P] NP[*]         : (lambda @ ($1 @ $2))
MP[P] -> M[P] NP[*]         : $2

# Q
Q[N] -> Num[N]            : $1

# AdjP
AdjP -> Adj               : $1
AdjP -> Deg Adj           : $1
