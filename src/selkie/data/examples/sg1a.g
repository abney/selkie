
% Rules

S -> NP[_n] VP[_n]        : (!qs ($2 $1))
NP[sg] -> Name            : $1
NP[_n] -> Det[_n] N[_n]   : (!q $1 @ ($2 @))
VP[_f] -> V[_f,i,0]       : $1
VP[_f] -> V[_f,t,0] NP[*] : (lambda @ ($1 @ $2))

% Lexicon

a Det[sg]        : some
barks V[sg,i,0]  : bark
cat N[sg]        : cat
chases V[sg,t,0] : chase
dog N[sg]        : dog
every Det[sg]    : every
Fido Name        : Fido
the Det[*]       : the

% Macros

every x R S: (forall x (if R S))
some x R S: (exists x (and R S))
