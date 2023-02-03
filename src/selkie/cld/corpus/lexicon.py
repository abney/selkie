##  @package seal.cld.corpus.lexicon
#   Provides the class Lexicon.

import os
from io import StringIO
from seal.core.io import pprint
from seal.app import PermissionDenied
from seal.cld.db.disk import writer, Loading
from seal.cld.db.file import File
from seal.cld.corpus.sim import LexicalIndices


#--  Utilities  ----------------------------------------------------------------

##  If x is not a list, return a list containing x.

def aslist (x):
    if isinstance(x, list): return x
    elif x is None: return []
    else: return [x]

##  Parse a PARID.  The input is a string containing two digits connected with
#   a dot.

def parse_parid (s):
    i = s.find('.')
    if i < 0: return s
    else: return (s[:i], int(s[i+1:]))

##  PARID to string.

def parid_string (par):
    return '%s.%d' % par

##  Parse a LEXID, which is FORM dot SENSE_NUMBER.

def parse_lexid (s):
    n = len(s)
    while n > 0 and s[n-1].isdigit(): n -= 1
    if n > 0 and s[n-1] == '.':
        form = s[:n-1]
        sense = int(s[n:])
    else:
        form = s
        sense = 0
    return (form, sense)


#--  Value Type  ---------------------------------------------------------------

##  Value types.

class ValueType (object):

    ##  Constructor.

    def __init__ (self, parse, tostring):

        ##  How to convert a string to a value of this type.
        self.parse = parse

        ##  How to convert a value of this type to a string.
        self.tostring = tostring

def _string_parse (x, lex):
    if isinstance(x, str): return x
    else: raise ValueError('Not a string: %s' % x)

def _string_tostring (x): return x

##  String value-type.
String = ValueType(_string_parse, _string_tostring)

def _xref_parse (x, lex):
    if isinstance(x, str):
        x = lex._intern(parse_lexid(x))
    if isinstance(x, LexicalEntry):
        return x
    else:
        raise ValueError('Not a LexicalEntry: %s' % x)

def _xref_tostring (x): return x._form + '.' + str(x._sense)

##  Cross-reference value-type.
XRef = ValueType(_xref_parse, _xref_tostring)

def _xrefs_parse (xs, lex):
    if isinstance(xs, str):
        return [_xref_parse(x, lex) for x in xs.split(' ')]
    elif (isinstance(xs, list) and
          all(isinstance(x, LexicalEntry) for x in xs)):
        return xs
    else:
        raise ValueError('Not a list of LexicalEntries: %s' % xs)

def _xrefs_tostring (xs): return ' '.join(_xref_tostring(x) for x in xs)

##  Value type representing a list of cross-references.
XRefs = ValueType(_xrefs_parse, _xrefs_tostring)


#--  Lexical Fields  -----------------------------------------------------------

##  A lexical field type.

class LexicalField (object):

    ##  Constructor.

    def __init__ (self, index, short, long, settable, inv, value):

        ##  The index in the record.
        self.index = index

        ##  The short name.
        self.short = short

        ##  The long name.
        self.long = long

        ##  Non-settable fields are automatically-computed backlinks.
        self.settable = settable

        ##  What field contains my backlinks, or what field this is backlink of.
        self.inv = inv

        ##  The value type.
        self.value = value

    ##  To make it hashable.

    def __hash__ (self): return hash(self.index)

    ##  To make it sortable.

    def __eq__ (self, other): return self.index == other.index

    ##  To make it sortable.

    def __le__ (self, other): return self.index <= other.index

    ##  String representation.

    def __repr__ (self): return 'LF.%s' % self.long


##  The lexical field for the gloss.
Gloss = LexicalField(0, 'ge', 'gloss', True, None, String)

##  The lexical field for the canonical form, if this is a variant form.
CanonicalForm = LexicalField(1, 'mn', '=', True, 5, XRef)

##  The lexical field for (morphological) components.
Components = LexicalField(2, 'mr', 'morph', True, 6, XRefs)

##  The lexical field for Which variety this is, if it is a variant form.
Variety = LexicalField(3, 'ue', 'variety', True, None, String)

##  The lexical field for the source of the lexical item.
Source = LexicalField(4, 'bb', 'source', True, None, String)

##  The automatically-generated field for variant forms that this is the canonical
#   form for.
VariantForms = LexicalField(5, 'va', 'variants', False, 1, XRefs)

##  The automatically-generated field for derived forms that contain this as
#   a (morphological) component.
DerivedForms = LexicalField(6, 'cf', 'derived', False, 2, XRefs)

##  The complete list of lexical fields.
lexical_fields = [Gloss, CanonicalForm, Components, Variety, Source, VariantForms, DerivedForms]
_lexical_fields_index = None

def _initialize_lexical_fields ():
    global lexical_fields, _lexical_fields_index
    for f in lexical_fields:
        if f.inv is not None:
            f.inv = lexical_fields[f.inv]
    _lexical_fields_index = {}
    for fld in lexical_fields:
        _lexical_fields_index[fld.short] = fld
        _lexical_fields_index[fld.long] = fld
        _lexical_fields_index[str(fld.index)] = fld

_initialize_lexical_fields()

##  Fetch a lexical field by name (if the input is a string) or by index (if the
#   input is an int).  If the input is a lexical field, it is passed through.

def get_lexical_field (x):
    global _lexical_fields_index
    if isinstance(x, LexicalField): return x
    elif isinstance(x, int): return lexical_fields[x]
    elif isinstance(x, str): 
        return _lexical_fields_index[x]
    else: raise Exception('Cannot convert to lexical field: %s' % x)


#--  Lexical Entries  ----------------------------------------------------------

##  A lexical entry.

class LexicalEntry (object):

    ##  Constructor.

    def __init__ (self, lexicon, index, form, sense):
        self._lexicon = lexicon
        self._index = index
        self._form = form
        self._sense = sense
        self._parids = []
        self._fields = {}
        
    ##  The lexicon it belongs to.
    def lexicon (self): return self._lexicon

    ##  The romanization it uses.
    def romanization (self): return self._lexicon.romanization()

    ##  The language its lexicon belongs to.
    def language (self): return self._lexicon.language()

    ##  Its index in the lexicon.
    def index (self): return self._index

    ##  Its form.
    def form (self): return self._form

    ##  Its sense number.
    def sense (self): return self._sense

    ##  Its LEXID: (form, sense_number).
    def key (self): return (self._form, self._sense)

    ##  The string form of its LEXID: FORM dot SENSE_NUMBER.
    def name (self): return self._form + '.' + str(self._sense)

    ##  The concordance list.  That is, places in the corpus where instances
    #   of the form occur, as a list of PARIDs.

    def parids (self): return self._parids

    ##  An entry is deletable if its form never occurs in the corpus.
    #   Note that a deletable entry may contain information in its lexical fields
    #   that cannot be reconstructed.

    def is_deletable (self): return not self._parids

    ##  An entry is empty if it is deletable and its lexical fields are empty.

    def is_empty (self): return not (self._parids or self._fields)

    ##  Dereferences the list of PARIDs to provide an iteration over paragraphs.

    def paragraphs (self):
        env = self.language().env
        for parid in self._parids:
            print('** parid=', repr(parid), 'env=', repr(env))
            try:
                par = env.deref_parid(parid)
                if par is not None:
                    yield par
            except PermissionDenied:
                pass
            except:
                raise

    ##  Always boolean true.

    def __bool__ (self): return True

    ##  For hashing purposes, the entry is equivalent to its key.

    def __hash__ (self): return hash((self._form, self._sense))

    ##  Compares keys.

    def __eq__ (self, other):
        if other is None: return False
        elif isinstance(other, LexicalEntry):
            return self._form == other._form and self._sense == other._sense
        else:
            raise Exception('Not comparable')

    ##  Compares keys.

    def __lt__ (self, other):
        if other is None: return False
        elif isinstance(other, LexicalEntry):
            return (self._form < other._form or
                    (self._form == other._form and self._sense < other._sense))
        else:
            raise Exception('Not comparable')

    ##  Fetch the value of a lexical field.  The key may be either a field
    #   name or field index.

    def __getitem__ (self, key):
        return self._fields.__getitem__(get_lexical_field(key))

    ##  Fetch, but return None if unsuccessful.

    def get (self, key):
        return self._fields.get(get_lexical_field(key))

    ##  Set the value of a lexical field.

    def __setitem__ (self, key, value):
        lex = self._lexicon
        with writer(lex):
            lex._set(self, key, value)

    ##  String representation.

    def __repr__ (self):
        return '<LexicalEntry %s %s>' % (self._form, self._sense)

    ##  Get the value of the gloss field.  Will follow canonical-form
    #   links to find a gloss.

    def get_gloss (self): 
        gloss = self._fields.get(Gloss)
        if gloss: return gloss
        alt = self._fields.get(CanonicalForm)
        if alt:
            gloss = alt._fields.get(Gloss)
            if gloss: return gloss

    ##  Returns the canonical form, if this is a variant form.

    def get_redirect (self):
        return self._fields.get(CanonicalForm)

    ##  Iterates over the fields that are not auto-generated.
    #   The iteration contains (key, value) pairs.

    def editable_fields (self):
        for (k,v) in self._fields.items():
            if k.settable:
                yield (k,v)

    ##  Iterates over all fields, including auto-generated ones.
    #   The iteration contains (key, value) pairs.

    def fields (self):
        return self._fields.items()

    def _field_strings (self, verbose=False):
        for (f,v) in self._fields.items():
            if verbose or f.settable:
                yield '%d=%s' % (f.index, f.value.tostring(v))

    ##  Returns a list containing string versions of the field values.

    def record (self):
        rec = [self.form(), self.sense()]
        for fs in self._field_strings():
            rec.append(fs)
        return rec

    ##  Returns a single string in which field values are separate by tabs.

    def string (self, verbose=False):
        if self._parids: ds = ','.join(parid_string(p) for p in self._parids)
        else: ds = ''
        flds = [self._form, str(self._sense), ds]
        flds.extend(self._field_strings(verbose=verbose))
        # for (f,v) in self._fields.items():
        #   if f.settable:
        #     flds.append(str(f.index) + '=' + f.value.tostring(v))
        return '\t'.join(flds)

    ##  Returns a human-readable string showing the contents.

    def pretty (self):
        with StringIO() as out:
            out.write('LexicalEntry %s %s:' % (self._form, self._sense))
            out.write('\n  pars: %s' % self._parids)
            if self._fields:
                out.write('\n  fields:')
                for (f,v) in self._fields.items():
                    out.write('\n    %s: %s' % (f, repr(v)))
            return out.getvalue()


#--  Lexicon  ------------------------------------------------------------------

##  A lexicon.

class Lexicon (File):

    ##  The language that it belongs to.

    def language (self): return self.env.language()

    ##  The romanization that it uses.

    def romanization (self): return self.env.romanization()

    #--  Read  -------------------------------------------------

    ##  Read the contents from a file.

    def __read__ (self, f):
        self._lexents = []
        self._indices = LexicalIndices(self)
        self._table = {}

        with Loading(self): # allows us to use self.modified()
            lex = self._table
            for line in f:
                fields = line.rstrip('\r\n').split('\t')
                form = fields[0]
                sense = int(fields[1])
                ent = self._intern((form, sense))
                if fields[2]:
                    for s in fields[2].split(','):
                        ent._parids.append(parse_parid(s))
                for field in fields[3:]:
                    i = field.index('=')
                    f = int(field[:i])
                    v = field[i+1:]
                    self._set(ent, f, v)

    def _intern (self, key, parid=None):
        (form, sense) = key
        assert isinstance(form, str) and isinstance(sense, int)
        lex = self._table

        # get the list of entries
        if form in lex:
            ents = lex[form]
        else:
            # if called during loading, the _modified flag will be cleared
            # at the end of __load__()
            self.modified()
            ents = lex[form] = []
            self._indices.add_form(form)

        # pad with None's
        if len(ents) <= sense:
            self.modified()
            while len(ents) <= sense:
                ents.append(None)

        # find or create new entry
        ent = ents[sense]
        if ent is None:
            self.modified()
            index = len(self._lexents)
            ent = ents[sense] = LexicalEntry(self, index, form, sense)
            self._lexents.append(ent)

        # add parid; it sets _modified if it does anything
        if parid is not None:
            self._add_parid(parid, ent)

        return ent

    def _add_parid (self, par, lexent):
        assert (isinstance(par, tuple) and
                len(par) == 2 and
                isinstance(par[0], str) and
                isinstance(par[1], int))
        if isinstance(lexent, tuple):
            # no par, to prevent recursive call to here
            lexent = self._intern(lexent)

        if lexent._parids is None:
            self.modified()
            lexent._parids = [par]
        elif par not in lexent._parids:
            self.modified()
            lexent._parids.append(par)

    # lexent may be LexicalEntry or lexid: (form, sensenum)
    # parid is used only if lexid is given; it is interned

    # f may be LexicalField or name or abbr

    # value will be parsed
    # value of None unsets

    def _set (self, lexent, f, value, parid=None):
        lexent = self._as_lexent(lexent, parid)
        assert lexent._lexicon is self
        if not isinstance(f, LexicalField):
            f = get_lexical_field(f)
        if not f.settable: raise Exception('Not settable: %s' % f)
        if value:
            value = f.value.parse(value, self)
        else:
            value = None
        old = lexent._fields.get(f)
        if old != value:
            self.modified()
            if value:
                lexent._fields[f] = value
            else:
                del lexent._fields[f]
                self._maybe_gc(lexent)
            if f.inv:
                self._update_backlinks(lexent, f, old, value)
            if f is Gloss:
                self._indices.replace_gloss(lexent, old, value)

    def _maybe_gc (self, lexent):
        if lexent.is_empty():
            self._delete_entry(lexent._form, lexent._sense)

    def _as_lexent (self, lexent, parid):
        if isinstance(lexent, tuple):
            lexent = self._intern(lexent, parid)
        if isinstance(lexent, LexicalEntry):
            return lexent
        else:
            raise Exception('Not a LexicalEntry: %s' % lexent)

    def _update_backlinks (self, lexent, f, oldvalue, newvalue):
        g = f.inv
        oldvalue = aslist(oldvalue)
        newvalue = aslist(newvalue)
        for v in oldvalue:
            if v not in newvalue:
                self._delete_backlink(v, g, lexent)
        for v in newvalue:
            if v not in oldvalue:
                self._add_backlink(v, g, lexent)
                
    def _add_backlink (self, lexent, f, value):
        flds = lexent._fields
        if f in flds:
            values = flds[f]
            if value not in values:
                values.append(value)
        else: values = flds[f] = [value]
    
    def _delete_backlink (self, lexent, f, value):
        flds = lexent._fields
        if f in flds:
            values = flds[f]
            try:
                i = values.index(value)
                if len(values) == 1:
                    del flds[f]
                else:
                    del values[i]
            except: pass
            self._maybe_gc(lexent)

    # only to be called if lexent is deletable

    def _delete_entry (self, form, sense):
        lex = self._table
        if form in lex:
            ents = lex[form]
            if sense < len(ents) and ents[sense] is not None:
                lexent = ents[sense]
                if not lexent.is_deletable():
                    raise Exception('Attempt to delete non-deletable entry')
                self.modified()
                self._lexents[lexent.index()] = None
                ents[sense] = None
                n = len(ents)
                while n > 0 and ents[n-1] is None: n -= 1
                if n == 0:
                    del lex[form]
                    self._indices.delete_form(form)
                elif n < len(ents):
                    del ents[n:]   # trailing None's

    #--  Write  ------------------------------------------------

    ##  Write the contents to a file.

    def __write__ (self, f):
        for ent in self._lexents:
            if not (ent is None or ent.is_empty()):
                f.write(ent.string())
                f.write('\n')


    #--  Modification  -----------------------------------------

    ##  Intern a reference to a lexical item.
    #   @arg x A LEXID: (form, sense_number).
    #   @arg parid A PARID: (TID, parnum).

    def intern (self, x, parid=None):
        with writer(self):
            return self._intern(x, parid)
        
    ##  Notify the lexicon that an instance of a lexical item has been deleted.

    def delete_parid (self, par, form, sense):
        with writer(self):
            if form in self._table:
                ents = self._table[form]
                if sense < len(ents):
                    ent = ents[sense]
                    if ent is not None:
                        try:
                            ent._parids.remove(par)
                            self.modified()
                            self._maybe_gc(ent)
                        except:
                            pass

    ##  Directly set values in the lexical entry.
    #   Unset by setting the value to None.

    def set_fields (self, form, sense, fields):
        with writer(self):
            lexent = self._intern((form, sense))
            for (f,v) in fields.items():
                self._set(lexent, f, v)

    #--  Access  -----------------------------------------------

    ##  Whether a lexical item with the given LEXID exists.

    def __contains__ (self, key):
        self.require_load()
        (lemma, seqno) = key
        lex = self._table
        if lemma not in lex: return False
        ents = lex[lemma]
        return seqno < len(ents) and ents[seqno] is not None

    ##  Fetch an entry by LEXID.
    #   @arg key If it is a LEXID, the return value is a LexicalEntry.
    #   If it is a string, it is taken to be a form, and the return value
    #   is a (possibly gappy) list of LexicalEntries indexed by sense number.

    def __getitem__ (self, key):
        self.require_load()
        lex = self._table
        if isinstance(key, str):
            return lex[key]
        else:
            (lemma, seqno) = key
            return lex[lemma][seqno]

    ##  Iterate over the LEXIDs.  (Not the lexical entry instances.)

    def __iter__ (self):
        self.require_load()
        for (form, ents) in self._table.items():
            for (i, ent) in enumerate(ents):
                if ent is not None:
                    yield (form, i)

    ##  Fetch by form or LEXID, but return None if unsuccessful.

    def get (self, key):
        self.require_load()
        lex = self._table
        if isinstance(key, str):
            if key in lex:
                return lex[key]
        else:
            (lemma, seqno) = key
            if lemma in lex:
                ents = lex[lemma]
                if seqno < len(ents): return ents[seqno]

    ##  Iteration over (LEXID, lexical entry) pairs.

    def items (self):
        self.require_load()
        for (form, ents) in self._table.items():
            for (i, ent) in enumerate(ents):
                if ent is not None:
                    yield ((form, i), ent)

    ##  Iteration over lexical entry instances.

    def entries (self):
        self.require_load()
        for ent in self._lexents:
            if ent is not None:
                yield ent

    ##  Iteration over forms (strings, not LEXIDS).

    def forms (self):
        self.require_load()
        return self._table.keys()

    ##  Returns the list of lexical entries whose form begins with the
    #   given letter.  The list is sorted by LEXID, which means alphabetically
    #   by form, and by sense number among lexical entries for the same form.

    def by_letter (self, letter):
        return sorted(form for form in self.forms() if form[0].lower() == letter)

    ##  Returns a list of lexical entries whose gloss contains the given gloss word.

    def by_gloss (self, gloss):
        self.require_load()
        return self._indices.lexents_by_gloss(gloss)

    ##  Returns the lexical entry with the given index.

    def by_index (self, index):
        self.require_load()
        return self._lexents[index]

    ##  Returns a list of glosses similar to the given gloss word(s), sorted
    #   by similarity.
    #   @arg minsim The cutoff for acceptable similarity.
    #   @arg exclude_self True by default.

    def similar_glosses (self, gloss, minsim=3, exclude_self=True):
        self.require_load()
        return self._indices.similar_glosses(gloss, minsim, exclude_self)

    ##  Returns a list of forms similar to the given one, sorted by similarity.

    def similar_forms (self, form, minsim=3, exclude_self=True):
        self.require_load()
        return self._indices.similar_forms(form, minsim, exclude_self)

    ##  Returns a list of lexical entries whose form or gloss is similar to
    #   the given form and gloss.

    def similar_to (self, form=None, gloss=None):
        self.require_load()
        return self._indices.lexents_like(form, gloss)
