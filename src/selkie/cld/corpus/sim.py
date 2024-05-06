##  @package seal.cld.corpus.sim
#   Implements the similarity functions used by the Lexicon.

##  Iterates over the skip 4-grams of the string.  For each position
#   in the string, four 4-grams are yielded: the next four characters,
#   the next three plus the fifth, the next two plus the fourth and fifth,
#   the next one plus the third through fifth.

def tuples (s):
    s = ' ' + s + ' '
    for i in range(len(s)-4):
        for ptn in ((0,1,2,3),(0,1,2,4),(0,1,3,4),(0,2,3,4)):
            yield s[i+ptn[0]] + s[i+ptn[1]] + s[i+ptn[2]] + s[i+ptn[3]]
    yield s[-4:]


##  An index mapping a skip 4-gram to a list of words containing that
#   4-gram.

class Index (object):

    ##  Constructor.

    def __init__ (self, table=None):
        self._index = {}
        if table:
            for key in table:
                self.add_key(key)

    ##  Fetch the words containing the given 4-tuple.

    def __getitem__ (self, key): return self._index.__getitem__(key)

    ##  Fetch, but return None on failure.

    def get (self, key): return self._index.get(key)

    ##  Index a new word.

    def add_key (self, key):
        index = self._index
        if len(key) >= 3:
            for t in set(tuples(key)):
                if t in index: index[t].append(key)
                else: index[t] = [key]
            
    ##  Delete a word from the index.  Affects the entries for all
    #   4-grams that it contains.

    def delete_key (self, key):
        index = self._index
        if len(key) >= 3:
            for t in set(tuples(key)):
                if t in index:
                    try:
                        lst = index[t]
                        i = lst.index(key)
                        if len(lst) == 1: del index[t]
                        else: del lst[i]
                    except:
                        pass

    ##  Computes a table containing all words that share any 4-grams
    #   with the given word.  The keys are ints n, and the values
    #   are words that share exactly n 4-grams with the given word.

    def similarity_table (self, key):
        tab = {}
        index = self._index
        for t in set(tuples(key)):
            if t in index:
                for form in index[t]:
                    if form in tab: tab[form] += 1
                    else: tab[form] = 1
        return tab


##  A set of indices for a lexicon.

class LexicalIndices (object):

    ##  Constructor.

    def __init__ (self, lexicon):

        ##  The lexicon.
        self.lexicon = lexicon

        ##  Maps forms to lists of similar forms.
        self.form_index = Index()

        ##  Maps gloss words to lists of similar glosses.
        self.gloss_index = Index()

        ##  Maps gloss words to lists of lexical entries.
        self.gloss_lexents = {}
        
#        lex = lexicon.contents()
#        for (form, lexents) in lex.items():
#            self.add_form(form)
#            for lexent in lexents:
#                gloss = lexent.get(0)
#                if gloss: self.add_gloss(lexent, gloss)

    ##  Add a gloss.

    def add_gloss (self, lexent, gloss):
        if gloss in self.gloss_lexents:
            self.gloss_lexents[gloss].append(lexent)
        else:
            self.gloss_index.add_key(gloss)
            self.gloss_lexents[gloss] = [lexent]

    ##  Delete a gloss.

    def delete_gloss (self, lexent, gloss):
        lexents = self.gloss_lexents[gloss]
        i = lexents.index(lexent)
        if len(lexents) == 1:
            self.gloss_index.delete_key(gloss)
            del self.gloss_lexents[gloss]
        else:
            del lexents[i]

    ##  Add a form.

    def add_form (self, form):
        self.form_index.add_key(form)

    ##  Delete a form.

    def delete_form (self, form):
        self.form_index.delete_key(form)

    ##  Replace a gloss.

    def replace_gloss (self, lexent, old, new):
        if old: self.delete_gloss(lexent, old)
        if new: self.add_gloss(lexent, new)

    ##  Fetch lexical entries by gloss.

    def lexents_by_gloss (self, gloss):
        return self.gloss_lexents.get(gloss)

    ##  Fetch glosses that are similar to the given one.

    def similar_glosses (self, gloss, minsim=3, exclude_self=True):
        assert gloss
        tab = self.gloss_index.similarity_table(gloss)
        return sorted(g for (g,v) in tab.items()
                      if v >= minsim and not (exclude_self and g == gloss))

    ##  Fetch forms that are similar to the given one.

    def similar_forms (self, form, minsim=3, exclude_self=True):
        assert form
        tab = self.form_index.similarity_table(form)
        return sorted(f for (f,v) in tab.items()
                      if v >= minsim and not (exclude_self and f == form))

    ##  Fetch lexical entries that have either a form or gloss that is
    #   similar to the given form and gloss.

    def lexents_like (self, form=None, gloss=None, reflexive=False, exclude=None):
        tab = {}
        if form:
            for (form2,v) in self.form_index.similarity_table(form).items():
                for lexent in self.lexicon[form2]:
                    tab[lexent] = v
        if gloss:
            for (gloss2,v) in self.gloss_index.similarity_table(gloss).items():
                for lexent in self.gloss_lexents[gloss2]:
                    if lexent in tab: tab[lexent] += v
                    else: tab[lexent] = v
        for (lexent,v) in tab.items():
            if v > 2 and (reflexive or form is None or lexent.form() != form):
                yield lexent
