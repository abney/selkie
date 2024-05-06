% Features
nform = sg/pl
vform = nform/ing
trans = i/t
bool = +/- default -
% Categories
S   []
NP  [form:nform, wh:bool]
VP  [form:vform]
V   [form:vform, trans:trans]
N   [form:nform]
Det [form:nform]
% Rules
S -> NP[_f] VP[_f]
NP[_f] -> Det[_f] N[_f]
VP[_f] -> V[_f,i]
VP[_f] -> V[_f,t] NP
% Lexicon
the Det
a Det[sg]
cat N[sg]
dog N[sg]
dogs N[pl]
barks V[sg,i]
chases V[sg,t]
