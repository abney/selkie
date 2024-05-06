
% Macros

every x R S: (forall x (if R S))
some x R S: (exists x (and R S))
nsome x R S: (not (exists x (and R S)))

% Rules

Start -> Root : $1
Start -> NP[*] : $1
Start -> PP[*] : $1
Start -> Greeting : ($1)

# Clauses
Root -> S[-]              : $1
Root -> YN                : (yn $1)
Root -> WhInv             : (wh @ (!g= @ $1))
Root -> Wh                : (wh @ (!g= @ $1))

YN -> Aux[_n,_v] NP[_n] VP[_v,-]            : (!qs ($3 $2))
YN -> Aux[_n,pred] NP[_n] AdjP             : (!qs ($3 $2))
YN -> Aux[_n,pred] NP[_n] PNom[*]           : (!qs ($3 $2))
WhInv -> WhNP[*] Aux[_n,_v] NP[_n] VP[_v,+]  : (!qs ($4 $3))
Wh -> WhNP[_n] VP[_n,-]                    : (!qs ($2 $g))
Wh -> WhNP[*] Aux[_n,pred] AdjP            : (!qs ($3 $g))
Wh -> WhNP[*] Aux[_n,pred] PNom[*]          : (!qs ($3 $g))

RC[*] -> RS                             : (lambda @ (!g= @ $1))
RS -> RelPron VP[*,-]                   : (!qs ($2 $g))
RC[*] -> RelPron S[+]                     : (lambda @ (!g= @ $2))

S[_g] -> NP[_n] VP[_n,_g]                  : (!qs ($2 $1))
S[-] -> S[-] Conj[*] S[-]                   : ($2 $1 $3)
S[-] -> Preconj[_t] S[-] Conj[_t] S[-]       : ($3 $2 $4)

# Verb complements
VP[_f,-] -> V[_f,i,-]            : $1
VP[_f,-] -> V[_f,t,-] NP[*]       : (lambda @ ($1 @ $2))
VP[_f,+] -> V[_f,t,-]            : (lambda @ ($1 @ $g))
VP[-f,-] -> V[_f,t,np] NP[*] NP[*] : (lambda @ ($1 @ $3 $2))
VP[_f,+] -> V[_f,t,np] NP[*]      : (lambda @ ($1 @ $g $2))
VP[_f,-] -> V[_f,i,P] PP[P]     : (lambda @ ($1 @ $2))
VP[_f,-] -> V[_f,t,_p] NP[*] MP[_p] : (lambda @ ($1 @ $2 $3))
VP[_f,+] -> V[_f,t,_p] MP[_p]      : (lambda @ ($1 @ $g $2))
VP[enp,-] -> V[enp,t,-] MP[by]     : (lambda @ ($1 $2 @))
VP[enp,-] -> V[enp,t,-]           : (lambda @ ($1 (!q exists @2 (person @2)) @))
VP[_f,_g] -> V[_f,i,_c] SC[_c,_g]  : (lambda @ ($1 @ (^ $2)))
VP[_f,_g] -> V[_f,t,_c] NP[*] SC[_c,_g] : (lambda @ ($1 @ (^ $3) $2))

VP[_f,_g] -> Aux[_f,_v] VP[_v,_g]   : $2
VP[_f,-] -> Aux[_f,pred] AdjP      : $2
VP[_f,-] -> Aux[_f,pred] PNom[*]    : $2

VP[_f,_g] -> Aux[_f,_v] PVR VP[_v,_g]   : (lambda @ ($2 ($3 @)))
VP[_f,-] -> Aux[_f,pred] PVR AdjP      : (lambda @ ($2 ($3 @)))
VP[_f,-] -> Aux[_f,pred] PVR PNom[*]    : (lambda @ ($2 ($3 @)))

# Adjuncts
#VP.$f -> VP.$f PP.*      : (mod $1 $2)
#VP.$f -> VP.$f AdvP      : (mod $1 $2)
#VP.$f -> VP.$f SC.*      : (mod $1 $2)

# NP
NP[sg] -> Name           : $1
NP[_n] -> Pron[_n]        : $1
NP[sg] -> QPron          : (!q $1 @)
NP[_n] -> Det[_n] Q[_n] N2[_n] : (!q $1 @ (and ($2 @) ($3 @)))
NP[_n] -> Det[_n] N2[_n]      : (!q $1 @ ($2 @))
NP[pl] -> Q[pl] N2[pl]        : (!q $1 @ ($2 @))
#NP.$n -> Det.$n Q.$n       : (!q $1 @ ($2 @))
NP[pl] -> N2[pl]             : (!q every @ ($1 @))
N2[_n] -> N2[_n] PP[loc]      : (lambda @ (and ($1 @) ($2 @)))
N2[_n] -> N2[_n] AdjP        : (lambda @ (and ($1 @) ($2 @)))
N2[_n] -> N2[_n] RC[_n]       : (lambda @ (and ($1 @) ($2 @)))
N2[_n] -> N1[_n]             : $1
N1[_n] -> Adj N1[_n]         : (lambda @ (and ($1 @) ($2 @)))
N1[_n] -> N[_n] MP[of]        : (lambda @ ($1 @ $2))
N1[_n] -> N[_n]              : $1

# PNom
PNom[sg] -> IndefArt N2[*]  : $2
PNom[pl] -> N2[pl]           : $1

# WhNP
WhNP[_n] -> WhPron[_n]       : $1

# PP
PP[_p] -> P[_p] NP[*]         : (lambda @ ($1 @ $2))
MP[_p] -> M[_p] NP[*]         : $2

# Q
Q[_n] -> Num[_n]            : $1

# AdjP
AdjP -> Adj               : $1
AdjP -> Deg Adj           : $1

% Lexicon

a        Det[sg] : some
a        IndefArt
all      Det[pl]   : every
am       Aux[1s,pred]
am       Aux[1s,ing]
am       Aux[1s,enp]
America  Name        : America
American N[sg]        : American
Americans N[pl]       : American
an       Det[sg]      : some
an       IndefArt
and      Conj[and]    : and
animal   N[sg]        : animal
animals  N[pl]        : animal
any      Det[sg]      : every
are      Aux[pl,ing]
are      Aux[pl,enp]
are      Aux[pl,pred]
baling   N[sg]        : baling
bark     V[pl,i,-]    : bark
bark     V[base,i,-]  : bark
barks    V[sg,i,-]    : bark
be       Aux[base,pred]
be       Aux[base,ing]
be       Aux[base,enp]
been     Aux[en,ing]
been     Aux[en,pred]
been     Aux[en,enp]
behind   P[loc]        : behind
being    Aux[ing,enp]
big      Adj          : big
Bill     Name         : Bill
black    Adj          : black
blue     Adj          : blue
bone     N[sg]         : bone
bones    N[pl]         : bone
book     N[sg]         : book
books    N[pl]         : book
both     Preconj[and]
bought   V[sg,t,-]         : buy
bought   V[pl,t,-]         : buy
bright   Adj          : bright
brown    Adj          : brown
by       M[by]
by       P[loc]        : by
cabinet  N[sg]         : cabinet
cabinets N[pl]         : cabinet
can      Aux[sg,base]
can      Aux[pl,base]
car      N[sg]         : car
cat      N[sg]         : cat
cats     N[pl]         : cat
caught   V[sg,t,-]         : catch
caught   V[pl,t,-]         : catch
chicken  N[sg]         : chicken
chickens N[pl]         : chicken
come     V[pl,i,-]         : come
could    Aux[sg,base]
could    Aux[pl,base]
counter  N[sg]         : counter
counters N[pl]         : counter
counting V[ing,t,-]        : count
country  N[sg]         : country
countries N[pl]        : country
cow      N[sg]         : cow
cows     N[pl]         : cow
criminal N[sg]         : criminal
criminals N[pl]        : criminal
Curiosity Name        : Curiosity
curiosity N[sg]        : Curiosity
dark     Adj          : dark
day      N[sg]         : day
days     N[pl]         : day
did      Aux[sg,base]
did      Aux[pl,base]
do       Aux[pl,base]
do       V[pl,t,-]
does     Aux[sg,base]
does     V[sg,t,-]
doing    V[ing,t,-]
dog      N[sg]         : dog
dogs     N[pl]         : dog
done     V[en,t,-]
eat      V[base,t,-]   : eat
eat      V[pl,t,-]     : eat
eats     V[sg,t,-]     : eat
either   Preconj[or]
enemy    N[sg]         : enemy
enemies  N[pl]         : enemy
every    Det[sg]       : every
fast     Adj          : fast
fast     Adv          : fast
foot     N[sg]         : foot
foot     Unit         : foot
feet     Unit         : foot
few      Q[pl]         : few
Fido     Name         : Fido
finished Adj          : finished
finished V[sg/pl,t,-]   : finish
fish     N[*]          : fish
for      P[for]        : for
friendly Adj          : friendly
garage   N[sg]         : garage
garages  N[pl]         : garage
gave     V[pl,t,to]         : give
gets     V[sg,t,-]         : get
gift     N[sg]         : gift
gifts    N[pl]         : gift
give     V[pl,t,to]         : give
good     Adj          : good
guitar   N[sg]         : guitar
guitars  N[pl]         : guitar
gum      N[sg]         : gum
gums     N[pl]         : gum
guy      N[sg]         : guy
guys     N[pl]         : guy
had      Aux[en,en]
had      V[sg/pl,t,-]
has      Aux[sg,en]
have     Aux[base,en]
he       Pron[sg]      : male
her      Pron[obj]     : female
her      Det[*]
hi       Greeting     : greeting
his      Det[*]
hold     V[pl,t,-]     : hold
hostile  Adj          : hostile
how      Deg
human    Adj          : human
human    N[sg]         : human
humans   N[pl]         : human
I        Pron[sg]
I        Pron[1sg]
in       P[in]         : in
incredibly Adv        : incredibly
is       Aux[sg,ing]
is       Aux[sg,enp]
is       Aux[sg,pred]
it       Pron[sg]
Jack     Name         : Jack
Jeeves   Name         : Jeeves
Jill     Name         : Jill
John     Name         : John
kills    V[sg,t,-]     : kill
kill     V[pl,t,-]     : kill
kill     V[base,t,-]   : kill
killing  V[ing,t,-]    : kill
killed   V[sg,t,-]     : kill
killed   V[pl,t,-]     : kill
killed   V[en,t,-]     : kill
killed   V[enp,t,-]    : kill
know     V[pl,t,-]         : know
know     V[pl,i,that]         : know
little   Adj          : little
little   Q[sg]         : little
long     Adj          : long
loves    V[sg,t,-]     : love
love     V[pl,t,-]     : love
love     V[base,t,-]   : love
loving   V[ing,t,-]    : love
loved    V[en,t,-]     : love
loved    V[enp,t,-]    : love
mangy    Adj          : mangy
many     Q[pl]         : many
Mary     Name         : Mary
Max      Name         : Max
missile  N[sg]         : missile
missiles N[pl]         : missile
money    N[sg]         : money
mortal   Adj          : mortal
movie    N[sg]         : movie
movies   N[pl]         : movie
much     Q[sg]         : much
murderer N[sg]         : murderer
murderers N[pl]        : murderer
never    Adv          : never
new      Adj          : new
no       Det[*]        : nsome
Nono     Name         : Nono
not      PVR          : not
now      Adv          : now
of       M[of]
old      Adj          : old
on       P[loc]        : on
one      Num[sg]       : one
one      N[sg]         : person
or       Conj[or]      : or
owns     V[sg,t,-]     : own
park     N[sg]         : park
parks    N[pl]         : parks
Pat      Name         : Pat
person   N[sg]         : person
persons  N[pl]         : person
people   N[pl]         : person
picnic   N[sg]         : picnic
picnics  N[pl]         : picnic
put      V[pl,t,loc]         : put
proud    Adj          : proud
quickly  Adv          : quick
rather   Deg
rawhide  N[sg]        : rawhide
red      Adj          : red
sand     N[sg]         : sand
sands    N[pl]         : sand
saw      V[sg,t,-]     : see
saw      V[pl,t,-]     : see
say      V[pl,i,that]         : say
see      V[pl,t,-]         : see
sells    V[sg,t,-]     : sell
sells    V[sg,t,to]    : sell
sells    V[sg,t,np]    : sell
sentimental Adj       : sentimental
several  Q[pl]         : several
Smith    Name         : Smith
so       Deg
Socrates Name         : Socrates
sofa     N[sg]         : sofa
sofas    N[pl]         : sofa
sold     V[sg,t,to]    : sell
sold     V[pl,t,to]    : sell
sold     V[sg,t,np]    : sell
sold     V[pl,t,np]    : sell
sold     V[enp,i,-]    : sell
some     Det[sg]       : some
Spot     Name         : Spot
star     N[sg]         : star
stars    N[pl]         : star
strap    N[sg]         : strap
straps   N[pl]         : strap
surely   Adv          : surely
take     V[pl,t,-]         : take
taken    V[en,t,-]         : take
taking   V[ing,t,-]        : take
tell     V[pl,t,that]         : tell
that     C[that]
that     Det[sg]       : that
that     Pron[sg]      : that
that     Deg
that     RelPron
the      Det[*]        : the
these    Det[pl]       : this
they     Pron[pl]      : they
three    Num[pl]       : three
thing    N[sg]         : thing
this     Det[sg]       : this
those    Det[pl]       : that
to       M[to]
to       Inf
took     V[sg,t,-]         : take
took     V[pl,t,-]         : take
top      N[sg]         : top
truce    N[sg]         : truce
truces   N[pl]         : truce
Tuna     Name         : Tuna
tuna     N[sg]         : tuna
twelve   Num[pl]       : twelve
twine    N[sg]         : twine
twinkling N[sg]        : twinkling
two      Num[pl]       : two
uneasy   Adj          : uneasy
very     Deg
wants    V[sg,i,inf]         : want
was      Aux[sg,pred]
was      Aux[sg,ing]
was      Aux[sg,enp]
washed   V[sg,t,-]         : wash
washed   V[pl,t,-]         : wash
watches  V[sg,t,-]         : watch
we       Pron[pl]      : we
weapon   N[sg]         : weapon
weapons  N[pl]         : weapon
were     Aux[pl,pred]
were     Aux[pl,ing]
were     Aux[pl,enp]
West     Name         : West
what     WhPron[sg]
when     WhAdv
whether  C[if]
which    WhDet        : wh
which    RelPron
white    Adj          : white
who      WhPron[sg]    : wh
who      RelPron
whom     WhPron[obj]   : wh
whom     RelPron
will     Aux[sg,base]
will     Aux[pl,base]
"won't"  Aux[sg,base]
"won't"  Aux[pl,base]
would    Aux[sg,base]
would    Aux[pl,base]
you      Pron[pl]      : you
Zeus     Name         : Zeus
