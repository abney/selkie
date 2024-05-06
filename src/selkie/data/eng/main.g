
% Rules


#--  Root  -----------------------------

root -> !adjp adjp
root -> !np np
root -> !num num
root -> !measp measp
root -> !pp pp
root -> !vp vp

root -> s
root -> aux[N,V] np[N] vp[V]
root -> np[wh:+] aux[N,V] np[N] vp[V,np]
root -> pp[P,wh:+] aux[N,V] np[N] vp[V,P]
root -> vp[base]


#--  NP  -------------------------------

np[N,W] -> n3[N,W] comma cadjp comma
np[pl] -> n3 conj n3
np[N,W] -> n3[N,W]

n3[N,W] -> pron[N,W]
n3[N] -> name[N]
n3[sg] -> fname lname
n3[sg] -> date

n3[N,W] -> det[N,W] n2[N]
n3[N,W] -> det[N,W] num[N] n2[N]
n3[N,W] -> num[N] n2[N]

n2[N] -> n2[N] rc
n2[N] -> n1[N]
n1[N] -> adj1 n1[N]
n1[N] -> n[N]

date -> month num2

measp -> num[F] unit[F]
measp -> num[F] unitp[F]

unitp[F] -> unitmod unit[F]


#--  PP  -------------------------------

pp[P,W] -> p[P] np[wh:W]
pp[P,-,np] -> p[P]


#--  AdjP  -----------------------------

adjp -> adj1
adjp -> cadjp

# complex adjp
cadjp -> adj1[P] pp[P]
cadjp -> measp adj1[P] pp[P]
cadjp -> measp adj1[X]

adj1[X] -> deg adj[X]
adj1[X] -> adj[X]


#--  Clauses  --------------------------

s -> np[N] vp[N]        : $2[arg1 $1]

sc[C] -> c[C] s
sc[inf] -> p[to] vp[base]
rc -> rpron[N] vp[N]
rc -> rpron np[N] vp[N,np]


#--  VP toplevel  ----------------------

# aux
vp[F,G] -> aux[F,V] vp[V,G]

vp[F,G] -> vp0[F,G]
vp0[F,G] -> vp0[F,G] date

#--  VP subcat  ------------------------

# simple intrans
vp0[F] -> v[F,i]

# simple trans
vp0[F] -> v[F,t] np
vp0[F,np] -> v[F,t]

# ditrans
vp0[F] -> v[F,t,np] np np
vp0[F,np] -> v[F,t,np] np

# intrans adjp
vp0[F] -> v[F,i,adj] adjp

# intrans pp
vp0[F,G] -> v[F,i,P] pp[P,gap:G]
vp0[F,P] -> v[F,i,P]

# trans pp
vp0[F,G] -> v[F,t,P] np pp[P,gap:G]
vp0[F,np] -> v[F,t,P] pp[P]
vp0[F,P] -> v[F,t,P] np

# intrans sc
vp0[F,G] -> v[F,i,C] sc[C,G]

# trans sc
vp0[F,G] -> v[F,t,C] np sc[C,G]
vp0[F,np] -> v[F,t,C] sc[C]
