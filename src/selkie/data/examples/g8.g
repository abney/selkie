
% Features

nform  = sg/pl
tns    = nform
vform  = tns/pl/base/en/psv/ing
pform  = about/loc/to/as
cform  = that/q/inf
trans  = i/t
select = pform/cform/adj/np/- default -
bool   = +/- default -
gap    = np/pform/- default -


% Categories

!adjp  []
!measp []
!np    []
!num   []

adj   [select:select]
adj1  [select:select]
adjp  []
aux   [form:vform, select:vform]
c     [form:cform]
cadjp []
comma []
conj  []
deg   []
det   [form:nform, wh:bool]
fname []
lname []
measp []
n     [form:nform]
n1    [form:nform]
n2    [form:nform]
n3    [form:nform, wh:bool]
name  [form:nform]
np    [form:nform, wh:bool]
num   [form:nform]
pron  [form:nform, wh:bool]
p     [form:pform]
pp    [form:pform, wh:bool, gap:gap]
rc    []
root  []
rpron [form:nform]
s     [gap:gap]
sc    [form:cform, gap:gap]
unit  [form:nform]
unitmod []
unitp [form:nform]
v     [form:vform, trans:trans, select:select]
vp    [form:vform, gap:gap]


% Rules

root -> !adjp adjp
root -> !np np
root -> !num num
root -> !measp measp

root -> s
root -> aux[N,V] np[N] vp[V]
root -> np[wh:+] aux[N,V] np[N] vp[V,np]
root -> pp[P,wh:+] aux[N,V] np[N] vp[V,P]
root -> vp[base]

s -> np[N] vp[N]

np[N,W] -> n3[N,W] comma cadjp comma
np[pl] -> n3 conj n3
np[N,W] -> n3[N,W]

n3[N,W] -> pron[N,W]
n3[N] -> name[N]
n3[sg] -> fname lname

n3[N,W] -> det[N,W] n2[N]
n3[N,W] -> det[N,W] num[N] n2[N]
n3[N,W] -> num[N] n2[N]


n2[N] -> n2[N] rc
n2[N] -> n1[N]
n1[N] -> adj1 n1[N]
n1[N] -> n[N]

pp[P,W] -> p[P] np[wh:W]
pp[P,-,np] -> p[P]

measp -> num[F] unit[F]
measp -> num[F] unitp[F]

unitp[F] -> unitmod unit[F]

adjp -> adj1
adjp -> cadjp

cadjp -> adj1[P] pp[P]
cadjp -> measp adj1[P] pp[P]
cadjp -> measp adj1[P]

adj1[P] -> deg adj[P]
adj1[P] -> adj[P]

sc[C] -> c[C] s
sc[inf] -> p[to] vp[base]
rc -> rpron[N] vp[N]
rc -> rpron np[N] vp[N,np]

# simple intrans
vp[F] -> v[F,i]

# simple trans
vp[F] -> v[F,t] np
vp[F,np] -> v[F,t]

# ditrans
vp[F] -> v[F,t,np] np np
vp[F,np] -> v[F,t,np] np

# intrans adjp
vp[F] -> v[F,i,adj] adjp

# intrans pp
vp[F,G] -> v[F,i,P] pp[P,gap:G]
vp[F,P] -> v[F,i,P]

# trans pp
vp[F,G] -> v[F,t,P] np pp[P,gap:G]
vp[F,np] -> v[F,t,P] pp[P]
vp[F,P] -> v[F,t,P] np

# intrans sc
vp[F,G] -> v[F,i,C] sc[C,G]

# trans sc
vp[F,G] -> v[F,t,C] np sc[C,G]
vp[F,np] -> v[F,t,C] sc[C]

# aux
vp[F,G] -> aux[F,V] vp[V,G]


% Lexicon

!adjp !adjp
!measp !measp
!np !np
!num !num

',' comma

a det[sg]
about p[about]
are aux[pl,ing/psv]
as p[as]
bark v[pl/base,i]
barks v[sg,i]
barked v[sg/pl/en,i]
barking v[ing,i]
be aux[base,ing/psv]
been aux[en,ing/psv]
being aux[ing,psv]
big adj
black adj
board n[sg]
cat n[sg]
cats n[pl]
chase v[pl/base,t]
chases v[sg,t]
chased v[sg/pl/en,t]
chased v[psv,i]
chasing v[ing,t]
did aux[sg/pl,base]
dog n[sg]
dogs n[pl]
fido name[sg]
gave v[sg/pl,t,np/to]
give v[pl/base,t,np/to]
giving v[ing,t,np/to]
happy adj[-/about]
has aux[sg,en]
have aux[pl/base,en]
he pron[sg]
in p[loc]
is v[sg,i,adj]
is aux[sg,ing/psv]
join v[pl/base,t,as/-]
joins v[sg,t,as/-]
max name[sg]
old adj[]
on p[loc]
pierre fname
puts v[sg,t,loc]
red adj
she pron[sg]
spot name[sg]
that c[that]
that rpron
the det
these det[pl]
thinks v[sg,i,about/that/-]
this det[sg]
those det[pl]
tells v[sg,t,about/that]
to p[to]
toy n[sg]
vinken lname
wants v[sg,i,inf]
we pron[sg]
what pron[sg,wh:+]
which det[wh:+]
white adj
who pron[sg,wh:+]
whom pron[sg,wh:+]
will n[sg]
will aux[sg/pl,base]
you pron[pl]

# Units

square unitmod
cubic unitmod
linear unitmod
standard unitmod
royal unitmod
english unitmod
metric unitmod

feet unit[pl]
foot unit[sg]
inch unit[sg]
inches unit[pl]
yard unit[sg]
yards unit[pl]
mile unit[sg]
miles unit[pl]

meter unit[sg]
meters unit[pl]
centimeter unit[sg]
centimeters unit[pl]
millimeter unit[sg]
millimeters unit[pl]
micrometer unit[sg]
micrometers unit[pl]
nanometer unit[sg]
nanometers unit[pl]
picometer unit[sg]
picometers unit[pl]
angstrom unit[sg]
angstroms unit[pl]
kilometer unit[sg]
kilometers unit[pl]

acre unit[sg]
acres unit[pl]

pound unit[sg]
pounds unit[pl]
ounce unit[sg]
ounces unit[pl]
ton unit[sg]
tons unit[pl]
tonne unit[sg]
tonnes unit[pl]

cup unit[sg]
cups unit[pl]
pint unit[sg]
pints unit[pl]
quart unit[sg]
quarts unit[pl]
gallon unit[sg]
gallons unit[pl]
peck unit[sg]
pecks unit[pl]
bushel unit[sg]
bushels unit[pl]
barrel unit[sg]
barrels unit[pl]
cord unit[sg]
cords unit[pl]

year unit[sg]
years unit[pl]
month unit[sg]
months unit[pl]
day unit[sg]
days unit[pl]
week unit[sg]
weeks unit[pl]
fortnight unit[sg]
fortnights unit[pl]
hour unit[sg]
hours unit[pl]
minute unit[sg]
minutes unit[pl]
second unit[sg]
seconds unit[pl]
millisecond unit[sg]
milliseconds unit[pl]
microsecond unit[sg]
microseconds unit[pl]
nanosecond unit[sg]
nanoseconds unit[pl]
picosecond unit[sg]
picoseconds unit[pl]

volt unit[sg]
volts unit[pl]
watt unit[sg]
watts unit[pl]
dyne unit[sg]
dynes unit[pl]
horsepower unit

karat unit[sg]
karats unit[pl]


#--  Numbers  ------------------------------------------------------------------

% Features

numform = sg/pl/cont
ndigits = 2/3/5/8


% Categories

zero         []
a            []
and          []
digit        [form:numform]
teen         []
ten          []
tens         []
num2         []
tail2        []
hundred      []
hundreds     []
ne-hundreds  []
num3         []
tail3        []
thousand     []
thousands    []
ne-thousands []
num5         []
tail5        []
million      []
millions     []
ne-millions  []
num8         []
tail8        []
billion      []
billions     []
ne-billions  []
num11        []
tail11       []
trillion     []
trillions    []
ne-trillions []


% Rules

tens -> ten digit
tens -> ten
tens -> teen

num2 -> tens
num2 -> digit

tail2 -> num2
tail2 -> and num2

hundreds -> digit hundred
hundreds -> digit hundred tail2
ne-hundreds -> a hundred
ne-hundreds -> a hundred tail2
ne-hundreds -> tens hundred
ne-hundreds -> tens hundred tail2

num3 -> hundreds
num3 -> num2

tail3 -> num3
tail3 -> and num3

thousands -> num3 thousand
thousands -> num3 thousand tail3
ne-thousands -> a thousand
ne-thousands -> a thousand tail3

num5 -> thousands
num5 -> num3

tail5 -> num5
tail5 -> and num5

millions -> num3 million
millions -> num3 million tail5
ne-millions -> a million
ne-millions -> a million tail5

num8 -> millions
num8 -> num5

tail8 -> num8
tail8 -> and num8

billions -> num3 billion
billions -> num3 billion tail8
ne-billions -> a billion
ne-billions -> a billion tail8

num11 -> billions
num11 -> num8

tail11 -> num11
tail11 -> and num11

trillions -> num3 trillion
trillions -> num3 trillion tail11
ne-trillions -> a trillion
ne-trillions -> a trillion tail11

num[pl] -> zero
num[F] -> digit[F]
num[pl] -> tens
num[pl] -> hundreds
num[pl] -> ne-hundreds
num[pl] -> thousands
num[pl] -> ne-thousands
num[pl] -> millions
num[pl] -> ne-millions
num[pl] -> billions
num[pl] -> ne-billions
num[pl] -> trillions
num[pl] -> ne-trillions


% Lexicon

and and

zero zero
a a

one digit[sg]
two digit[pl]
three digit[pl]
four digit[pl]
five digit[pl]
six digit[pl]
seven digit[pl]
eight digit[pl]
nine digit[pl]

ten teen
eleven teen
twelve teen
thirteen teen
fourteen teen
fifteen teen
sixteen teen
seventeen teen
eighteen teen
nineteen teen

twenty ten
thirty ten
forty ten
fifty ten
sixty ten
seventy ten
eighty ten
ninety ten

hundred hundred
thousand thousand
million million
billion billion
trillion trillion
