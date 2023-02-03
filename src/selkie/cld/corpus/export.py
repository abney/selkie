##  @package seal.cld.corpus.export
#
#  See items.html for general discussion.
#
#  The toplevel calls are the com_list, com_export, com_delete, and com_import
#  methods of Corpus.  The first three take selections as arguments.  The
#  selection is turned into an iteration over Items, and the corresponding
#  Item method is called: com_list, com_export, com_delete, or com_import.
#
#  A <b>selection</b> is a list of pairs (<i>cn, ids</i>), where <i>cn</i>
#  is a container name and <i>ids</i> is a list of IDs.  It is turned into
#  a list of items by passing it to the Corpus.items method.
#
#  The Corpus.items method iterates over the pairs (<i>cn, ids</i>).
#  It fetches the named container and calls the Container.items
#  method with <i>ids</i> as argument.  If the selection is empty, it
#  iterates over all containers and calls the Container.items method
#  with an empty <i>ids</i> list.
#
#  The Container.items method, if given an empty ID list, iterates over all
#  descendants.  Otherwise, it iterates over the given IDs, calls get_item
#  to turn each ID into an item, and then iterates over the descendants of
#  each selected item.
#
#  From this description, one can see that one requires both Container and
#  Item to implement children and descendants methods.  To avoid redundancy,
#  they are implemented as methods of Node, and both Item and Container inherit
#  from Node.


import sys, os
from seal.core.io import pprint
from seal.cld.db.disk import writer
from seal.cld.corpus.rom import Romanization, ReadOnlyRomanization
from seal.cld.corpus.language import Language
from seal.cld.corpus.lexicon import lexical_fields, Lexicon
from seal.cld.corpus.token import Token


#--  ExportStream  -------------------------------------------------------------

##  A stream that writes an export file.

class ExportStream (object):

    ##  Constructor.

    def __init__ (self, fn):

        ##  The filename.
        self.filename = fn

        self._file = None
        self._do_close = None

    ##  Enter.  Opens the file for writing.

    def __enter__ (self):
        fn = self.filename
        if fn == '-':
            self._file = sys.stdout
            self._do_close = False
        else:
            self._file = open(fn, 'w')
            self._do_close = True
        return self

    ##  Exit.  Closes the file, unless it is stdout.

    def __exit__ (self, t, v, tb):
        if self._do_close:
            self._file.close()
        self._file = None

    ##  Write a record to the file.

    def write_record (self, *fields):
        f = self._file
        first = True
        for field in fields:
            if first: first = False
            else: f.write('\t')
            f.write(str(field))
        f.write('\n')


##  A stream that is reading from an export file.
#   An ImportStream generates two callbacks.  The corpus's
#   intern_item method is called for each 'I' record, and the
#   com_import method of the returned item is called.

class ImportStream (object):

    ##  Constructor.

    def __init__ (self, fn, corpus):
        self._corpus = corpus
        self._filename = fn
        self._file = None
        self._do_close = None
        self._lookahead = None
        self._linenum = 0

        # item corresponding to most recent 'I' record
        self._item = None
        self._item_type = None
        self._item_subtype = None

    ##  The corpus.
    def corpus (self): return self._corpus

    ##  The export file's filename.
    def filename (self): return self._filename

    ##  The current line number.
    def linenum (self): return self._linenum

    ##  The item corresponding to the most recent 'I' record.
    def item (self): return self._item

    ##  Its type.
    def item_type (self): return self._item_type

    ##  Its subtype.
    def item_subtype (self): return self._item_subtype

    ##  The file-internal name for an item.

    def internal_name (self, xid=None):
        if xid is None:
            return self._item.name()
        else:
            return self._id_map[xid]

    ##  Opens the file for reading.

    def __enter__ (self):
        if self._filename == '-':
            self._file = sys.stdin
            self._do_close = False
        else:
            self._file = open(self._filename, 'r')
            self._do_close = True
        return self

    ##  Closes the file, unless it is stdin.

    def __exit__ (self, t, v, tb):
        if self._do_close:
            self._file.close()
        self._file = None

    ##  Iterate over the records.

    def __iter__ (self):
        return self

    ##  Look at the next record without consuming it.

    def peek (self):
        if self._lookahead is None:
            try:
                line = next(self._file)
                self._lookahead = line.rstrip('\n').split('\t')
            except StopIteration:
                self._lookahead = ['EOF']
        return self._lookahead

    ##  Are we looking at a record with type c?

    def looking_at (self, c):
        rec = self.peek()
        return rec[0] in c

    ##  Advance to the next record.

    def advance (self):
        if not (self._lookahead is None or self._lookahead[0] == 'EOF'):
            self._lookahead = None
            self._linenum += 1

    ##  Return the current record and advance.

    def read_record (self):
        rec = self.peek()
        self.advance()
        return rec

    ##  The iterator method.

    def __next__ (self):
        rec = self.read_record()
        if rec[0] == 'EOF':
            raise StopIteration
        elif rec[0] == 'Z':
            rec = self.read_record()
            if rec[0] != 'EOF':
                print("Warning: stay material after 'Z' record")
            raise StopIteration
        elif rec[0] != 'I':
            raise Exception("Expecting an 'I' record: %s" % rec)

        (_, type, cn, id, subtype, path) = rec
        self._item_type = type
        self._item_subtype = subtype

        pprint('Intern', type, cn, id, subtype, path)
        with pprint.indent():
            self._item = item = self._corpus.intern_item(cn, id, path)
            if item.type() != type:
                raise Exception("Wrong type, expecting '%s': %s" % (type, repr(item)))

        newid = item.id()
        newpath = item.path()
        pprint('Import', type, cn, '%s->%s' % (id, newid), subtype, '%s->%s' % (path, newpath))
        with pprint.indent():
            item.com_import(ItemRecords(self))

        return item

    ##  Signal an error.  Show the current line number and record.

    def error (self, msg, rec):
        raise Exception('[%d] %s: %s' % (self._linenum, msg, rec))


##  Transforms a stream into an iteration over item records.

class ItemRecords (object):

    ##  Constructor.

    def __init__ (self, stream):

        ##  The original stream.
        self.stream = stream

    ##  Returns self.

    def __iter__ (self):
        return self

    ##  Iteration method.

    def __next__ (self):
        rec = self.stream.peek()
        if rec[0] in ('EOF', 'I'):
            raise StopIteration
        self.stream.advance()
        return rec

    ##  Peek.

    def peek (self): return self.stream.peek()

    ##  Whether looking at record of type c.

    def looking_at (self, c): return self.stream.looking_at(c)

    ##  Signal error, indicating line number.

    def error (self, msg, rec): self.stream.error(msg, rec)

    ##  Return a substream containing only a block of following records whose
    #   types are all in the list given.

    def restrict_to (self, rectypes):
        return RecordBlock(self.stream, rectypes)

    ##  Get the current item.

    def item (self): return self.stream.item()

    ##  Get its type.

    def item_type (self): return self.stream.item_type()

    ##  Get its subtype.

    def item_subtype (self): return self.stream.item_subtype()

    ##  Get its ID.

    def item_id (self, xid=None): return self.stream.item_id(xid)
        

##  A slice of a stream.

class RecordBlock (ItemRecords):

    ##  Constructor.

    def __init__ (self, stream, rectypes):
        ItemRecords.__init__(self, stream)

        ##  The record types included in this slice.
        self.rectypes = rectypes

    ##  Iteration method.

    def __next__ (self):
        rec = self.stream.peek()
        if rec[0] in self.rectypes:
            self.stream.advance()
            return rec
        else:
            raise StopIteration


#--  Node  ---------------------------------------------------------------------

##  A node in the object hierarchy.

class Node (object):

    ##  Constructor.

    def __init__ (self, parent, file):

        ##  The parent node.
        self.parent = parent

        ##  The file it belongs to.
        self.file = file

    ##  Specializations may override.  It should return an iteration over
    #   Items.  The default implementation returns the empty list.

    def children (self):
        return []

    ##  Transitive closure over children.

    def descendants (self):
        out = []
        self._collect_descendants(out)
        return out

    def _collect_descendants (self, out):
        if isinstance(self, Item):
            out.append(self)
        for child in self.children():
            child._collect_descendants(out)

    ##  The name of the language that this node belongs to.

    def language_name (self):
        return self.file.env.language().name()


#--  Container  ----------------------------------------------------------------

##  A Container is a collection of Items.  It wraps a corpus directory.

class Container (Node):

    ##  The name is a string that uniquely identifies one of the items.
    #   In most cases, it is simply an ID, but in the particular case of the
    #   corpus, a name is a pair of form (<i>cn, id</i>), where
    #   <i>cn</i> is a container name and <i>id</i> is an item ID within the
    #   named container.

    def get_item (self, name):
        raise Exception("Specializations must override 'get_item': %s" % repr(self))

    ##  Like get_item, but this is called during import; it should
    #   create a new item if necessary.  The returned item need not have
    #   the requested ID; the association between stream ID and corpus ID
    #   will be recorded in the ImportStream.

    def intern_item (self, id, path):
        raise Exception("Specializations must override 'intern_item': %s" % repr(self))

    ##  The argument is a selection.  If the selection is empty, this
    #   returns an iteration over all items.  Otherwise, the selection is
    #   a list of item IDs.  The named items are fetched and an iteration
    #   is done over their descendants.  Returns an iteration over descendants
    #   of the selected items.  An error is signalled if an ID names no item,
    #   but duplicates are not detected.

    def items (self, sel=None):
        if sel:
            for id in sel:
                item = self.get_item(id)
                if item is None:
                    raise Exception('No such item: %s/%s' % (self.file.name(), id))
                for desc in item.descendants():
                    yield desc
        else:
            for desc in self.descendants():
                yield desc


#--  Corpus  -------------------------------------------------------------------

##  Item view of a Corpus.

class CorpusContainer (Container):

    ##  Constructor.

    def __init__ (self, corpus):
        Container.__init__(self, None, corpus)

        ##  The romanization items.
        self.roms = RegistryContainer(self, self.file.roms)

        ##  The GLab items.
        self.glab = GLabContainer(self, self.file.glab)

        ##  The language items.
        self.langs = dict((name, LanguageContainer(self, lang))
                          for (name, lang) in corpus.langs.items())

    ##  An iterator over the children.

    def children (self):
        yield self.roms
        yield self.glab
        for lang in self.langs.values():
            yield lang

    ##  Get a container by name: 'roms', 'glab', or a language ID.

    def get_container (self, name):
        if name == 'roms': return self.roms
        elif name == 'glab': return self.glab
        elif name in self.langs: return self.langs[name]

    ##  Intern a container by name.

    def intern_container (self, name):
        if name == 'roms': return self.roms
        elif name == 'glab': return self.glab
        elif name in self.langs: return self.langs[name]
        else:
            lang = self.file.langs.new_child(name)
            cont = self.langs[name] = LanguageContainer(self, lang)
            return cont

    ##  This overrides Container.items.  An example of the list of
    #   selected items: <tt>['roms/salish', 'deu', 'oji/1'].</tt>
    #   A selector like <tt>'deu'</tt> does not identify a single
    #   item but rather all items in a container; hence it needs special
    #   treatment.</p>
    #
    #   Item selectors are expanded to pairs, e.g. <tt>('oji', '1').</tt></p>

    def get_items (self, sel=None):
        if sel:
            for id in sel:
                fullname = id.split('/')
                # container name
                if len(fullname) == 1:
                    cont = self.get_container(fullname[0])
                    for item in cont.get_items():
                        for desc in item.descendants():
                            yield desc
                elif len(fullname) == 2:
                    item = self.get_item(fullname)
                    if item is None:
                        raise Exception('No such item: %s/%s' % (self.file.name(), id))
                    for desc in item.descendants():
                        yield desc
                else:
                    raise Exception('Bad ID: %s' % id)
        else:
            for desc in self.descendants():
                yield desc

    ##  Get an item.  Fullname is a pair (container, ID).

    def get_item (self, fullname):
        (cn, id) = fullname
        cont = self.get_container(cn)
        if cont is not None:
            return cont.get_item(id)

    ##  Intern an item.

    def intern_item (self, cn, id, path):
        return self.intern_container(cn).intern_item(id, path)

    ##  The implementation of the 'list' command of cld.

    def com_list (self, *sel):
        for item in self.items(sel):
            item.com_list()
    
    ##  The implementation of the 'delete' command of cld.

    def com_delete (self, *sel):
        for item in self.items(sel):
            item.com_delete()

    ##  The implementation of the 'export' command of cld.

    def com_export (self, fn, *sel):
        with ExportStream(fn) as stream:
            for item in self.items(sel):
                item.com_export(stream)
            stream.write_record('Z', 'End of export')

    ##  The implementation of the 'import' command of cld.
    #   Currently ignores any selection.

    def com_import (self, fn, *sel):
        with ImportStream(fn, self) as stream:
            for item in stream:
                pass


#--  RegistryContainer  --------------------------------------------------------

##  A container for romanization items.

class RegistryContainer (Container):

    ##  Iterator over RomItems.

    def children (self):
        for rom in self.file.children():
            yield RomItem(self, rom)

    ##  Returns the named RomItem, or None.

    def get_item (self, name):
        roms = self.file
        if name in roms:
            return RomItem(self, roms[name])

    ##  Returns the named RomItem, creating a new one if necessary.

    def intern_item (self, id, path):
        assert not path
        rom = self.get_item(id)
        if rom is None:
            rom = RomItem(self, self.file.new_child(id))
        return rom


#--  LanguageContainer  --------------------------------------------------------

##  A container corresponding to a language.

class LanguageContainer (Container):

    ##  Constructor.

    def __init__ (self, *args):
        Container.__init__(self, *args)
        self._sidmap = None

    def _lexicon (self):
        return LexiconItem(self, self.file.lexicon)

    def _language (self):
        return LanguageItem(self, self.file._info)

    def _texts (self):
        for text in self.file.all_texts():
            yield TextItem(self, text)

    def _get_text (self, id):
        idx = self.file.env.index()
        txt = idx['txt'].get(id)
        return TextItem(self, txt)

    ##  Id may be 'lexicon', 'language', or a text ID.

    def get_item (self, id):
        if id == 'lexicon':
            return self._lexicon()
        elif id == 'language':
            return self._language()
        else:
            return self._get_text(id)

    ##  Fetch an item, creating a new one if necessary.

    def intern_item (self, sid, path):
        if self._sidmap is None:
            self._sidmap = {'lexicon': self._lexicon(),
                            'language': self._language()}
        if sid in self._sidmap:
            return self._sidmap[sid]
        else:

            path = path.split('/')
            last = len(path) - 1
            assert sid == path[last]
            i = last - 1

            # search back for a known path[i]
            while i >= 0 and path[i] not in self._sidmap:
                i -= 1

            # none are known
            if i < 0:
                toc = self.file.texts

            # item = the last known text
            else:
                item = self._sidmap[path[i]]
                text = item.file
                if 'toc' in text:
                    toc = text['toc']
                else:
                    toc = text.new_child('toc')

            # allocate new tocs for unknown path components before last
            i += 1
            while i < last:
                item = self._sidmap_alloc(path[i], toc)
                i += 1
                toc = item.file.new_child('toc')

            # allocate item for last
            return self._sidmap_alloc(path[last], toc)

    def _sidmap_alloc (self, sid, toc):
        text = toc.new_child()
        item = TextItem(self, text)
        self._sidmap[sid] = item
        return item

    ##  Iterate over the items in the container.

    def children (self):
        yield self._language()
        yield self._lexicon()
        for txt in self._texts():
            yield txt


def _pretty_key (item):
    name = item.name()
    if name and name[0].isdigit():
        return ' ' * (10 - len(name)) + name
    else:
        return name


#--  GLabContainer  ------------------------------------------------------------

##  Container for GLab notebooks.

class GLabContainer (Container):

    ##  Constructor.

    def __init__ (self, *args):
        Container.__init__(self, *args)
        self._sidmap = None

    ##  Iterates over NotebookItems.

    def children (self):
        glab = self.file
        for lib in glab.children():
            for nb in lib.children():
                yield NotebookItem(self, nb)

    ##  Fetch a NotebookItem by name.

    def get_item (self, name):
        glab = self.file
        i = name.find('-')
        if i > 0 and i < len(name)-1:
            username = name[:i]
            nbname = name[i+1:]
            if username in glab:
                return NotebookItem(self, glab[username].get(nbname))

    ##  Fetch a NotebookItem by name, creating a new one if necessary.

    def intern_item (self, sid, path):
        assert not path
        if self._sidmap is None:
            self._sidmap = {}
        if sid in self._sidmap:
            return self._sidmap[sid]
        (user, n) = sid.split('/')
        glab = self.file
        if user in glab:
            lib = glab[user]
        else:
            lib = glab.new_child(user)
        nb = lib.new_child()
        item = NotebookItem(self, nb)
        self._sidmap[sid] = item
        return item


#--  Item  ---------------------------------------------------------------------

##  Export item.

class Item (Node):

    ##  Type.  Must be overridden by specializations.

    def type (self):
        raise Exception("Specializations must override 'type': %s" % repr(self))

    ##  Subtype.  The empty string, by default.

    def subtype (self): return ''

    ##  Path.  The empty string, by default.

    def path (self): return ''

    ##  Container ID.  Specializations may override.  Default implementation
    #   returns the language name.

    def cn (self):
        return self.language_name()

    ##  Item ID.  Specializations may override.

    def id (self):
        return self.file.name()

    ##  The item record.  (type, CN, ID, subtype, path).

    def record (self):
        return (self.type(), self.cn(), self.id(), self.subtype(), self.path())

    ##  Create a string from the record for inclusion in a listing.

    def com_list (self):
        pprint('%-8s %-8s %-10s %-8s %s' % self.record())

    ##  Write the beginning of an item (an 'I' record) to the stream.

    def start_block (self, stream):
        stream.write_record('I', *self.record())

    ##  Export the item to the stream.  Specializations must override.

    def com_export (self, stream):
        raise Exception("Specializations must override 'com_export': %s" % repr(self))

    ##  Delete the item.  Specializations must override.

    def com_delete (self):
        raise Exception("Specializations must override 'com_delete': %s" % repr(self))

    ##  Import the item from the stream.  Specializations must override.

    def com_import (self, stream):
        raise Exception("Specializations must override 'com_import': %s" % repr(self))



#--  RomItem  ------------------------------------------------------------------

##  An item representing a romanization.

class RomItem (Item):

    ##  Type is 'rom'.

    def type (self): return 'rom'

    ##  Container ID is 'roms'.

    def cn (self): return 'roms'

    ##  Write a block of 'R' records.

    def com_export (self, stream):
        rom = self.file
        self.start_block(stream)
        for (k,v) in rom.items():
            stream.write_record('R', k, v)

    ##  Read a block of 'R' records.

    def com_import (self, stream):
        rom = self.file
        with writer(rom):
            for rec in stream.restrict_to('R'):
                if len(rec) != 3: stream.error('Expecting k v', rec)
                (_, k, v)  = rec
                rom[k] = v


#--  LanguageItem  -------------------------------------------------------------

##  An item representing a language.

class LanguageItem (Item):

    ##  Type is 'language'.

    def type (self): return 'language'

    ##  ID is 'language'.

    def id (self): return 'language'

    ##  Write a block of 'M' records.

    def com_export (self, stream):
        info = self.file
        self.start_block(stream)
        for (k,v) in info.items():
            stream.write_record('M', k, v)

    ##  Read a block of 'M' records.

    def com_import (self, stream):
        info = self.file
        with writer(info):
            for rec in stream.restrict_to('M'):
                if len(rec) != 3: stream.error('Expecting k v', rec)
                (_,k,v) = rec
                info[k] = v


#--  LexiconItem  --------------------------------------------------------------

##  An item representing a lexicon.

class LexiconItem (Item):

    ##  Type is 'lexicon'.

    def type (self): return 'lexicon'

    ##  Write a block of 'F' and 'L' records.

    def com_export (self, stream):
        lexicon = self.file
        self.start_block(stream)
        for lf in lexical_fields:
            stream.write_record('F', lf.index, lf.long)
        # load
        for ent in lexicon.entries():
            fields = ent.record()
            stream.write_record('L', *fields)

    ##  Read a block of 'F' and 'L' records.

    def com_import (self, stream):
        lex = self.file
        for rec in stream.restrict_to('F'):
            if len(rec) != 3: stream.error('Expecting i long', rec)
            (_, i, long) = rec
            if not i.isdigit(): stream.error('Expecting int i', rec)
            i = int(i)
            if not lexical_fields[i].long == long:
                stream.error('Wrong long form of lex field', rec)
        with writer(lex):
            for rec in stream.restrict_to('L'):
                key = (rec[1], int(rec[2]))
                lexent = lex._intern(key)
                for s in rec[3:]:
                    k = s.index('=')
                    i = int(s[:k])
                    f = lexical_fields[i]
                    value = s[k+1:]
                    lex._set(lexent, f, value)


#--  TextItem  -----------------------------------------------------------------

##  An item representing a text.

class TextItem (Item):

    ##  Type is 'text'.

    def type (self): return 'text'

    ##  Subtype is the file type: 'orig', 'media', or 'toc'.

    def subtype (self): return self.file.type()

    ##  Path is langs/LLL/texts/.

    def path (self):
        path = self.file.logrelpath()
        pfx = 'langs/' + self.language_name() + '/texts/'
        assert path.startswith(pfx)
        return path[len(pfx):].replace('/toc/', '/')

    ##  Delete it.

    def com_delete (self):
        toc = self.parent()
        assert isinstance(toc, Toc)
        i = toc.child_index(self)
        with toc.writer() as w:
            w.delete_child(i)

    ##  Write the text.

    def com_export (self, stream):
        text = self.file
        subtype = text.type()
        self.start_block(stream)

        # info
        self._export_info(text.info(), stream)

        if subtype == 'orig':
            self._export_token_file(text.orig, stream)
            if text.trans:
                self._export_trans_file(text.trans, stream)

        elif subtype == 'media':
            self._export_media_file(text.media, stream)
            xs = text.get('xscript')
            if xs is not None:
                self._export_transcription_dir(xs, stream)
            trans = text.get('trans')
            if trans is not None:
                self._export_trans_file(trans, stream)

        elif subtype == 'toc':
            pass

    ##  Read a text.

    def com_import (self, stream):
        text = self.file
        subtype = stream.item_subtype()
        self._import_info(text.info(), stream)
        if subtype == 'orig':
            self._import_token_file(text.new_child('orig'), stream)
            if stream.looking_at('E'):
                self._import_trans_file(text.new_child('trans'), stream)
        elif subtype == 'media':
            self._import_media_file(text.new_child('media'), stream)
            if stream.looking_at('CST'):
                self._import_transcription_dir(text.new_child('xscript'), stream)
            if stream.looking_at('E'):
                self._import_trans_file(text.new_child('trans'), stream)

    # TextInfo

    def _export_info (self, info, stream):
        for (k,v) in info.items():
            stream.write_record('P', k, v)

    def _import_info (self, info, stream):
        with writer(info):
            for rec in stream.restrict_to('P'):
                if len(rec) != 3: stream.error('Expecting k v', rec)
                (_,k,v) = rec
                info[k] = v

    # TokenFile

    def _export_token_file (self, tf, stream):
        for blk in tf.blocks():
            stream.write_record('S')
            for tok in blk:
                stream.write_record('T', tok.form(), tok.sense(), tok.lpunc(), tok.rpunc())

    def _import_token_file (self, tf, stream):
        with writer(tf):
            block = None
            for rec in stream.restrict_to('ST'):
                if rec[0] == 'S':
                    block = tf.allocate()
                elif rec[0] == 'T':
                    if block is None:
                        stream.error("'T' record must be preceded by 'S' record", rec)
                    if len(rec) != 5:
                        stream.error('Expecting form sense lpunc rpunc', rec)
                    (_, form, sense, lpunc, rpunc) = rec
                    block.append(Token(form, int(sense), lpunc, rpunc))
                else:
                    raise Exception('Restrict_to is broken')

    # Translation

    def _export_trans_file (self, trans, stream):
        for s in trans:
            stream.write_record('E', s)

    def _import_trans_file (self, trans, stream):
        with writer(trans):
            for rec in stream.restrict_to('E'):
                if len(rec) != 2: stream.error('Expecting s', rec)
                (_,s) = rec
                trans.append(s)

    # MediaFile

    def _export_media_file (self, mf, stream):
        for (suf, (uname, fname)) in mf.items():
            stream.write_record('A', suf, uname, fname)
        dflt = mf.get_default()
        if dflt:
            stream.write_record('A', '__default__', dflt)

    def _import_media_file (self, mf, stream):
        with writer(mf):
            for rec in stream.restrict_to('A'):
                if rec[1] == '__default__':
                    if len(rec) != 3:
                        stream.error('Expecting 1 value', rec)
                    mf.set_default(rec[2])
                else:
                    if len(rec) != 4:
                        stream.error('Expecting suffix username fname', rec)
                    (_, suffix, username, fname) = rec
                    mf.set(username, fname)

    # Transcription

    def _export_transcription_dir (self, xs, stream):
        n = len(xs.clips)
        for i in range(n):
            clip = xs.clips[i]
            para = xs.paras[i]
            stream.write_record('C', clip.start, clip.end, para)
        self._export_token_file(xs.transcript, stream)

    def _import_transcription_dir (self, xs, stream):
        clips = xs.clips
        paras = xs.paras
        transcript = xs.transcript
        with writer(clips, paras):
            for rec in stream.restrict_to('C'):
                (_, start, end, para) = rec
                clips.new_clip(float(start), float(end))
                # Legacy
                if para == 'True': para = 'S'
                elif para == 'False': para = 'W'
                paras.append(para)
        self._import_token_file(transcript, stream)


#--  NotebookItem  -------------------------------------------------------------

##  Item representing a GLab notebook.

class NotebookItem (Item):

    ##  Type is 'notebook'.

    def type (self): return 'notebook'

    ##  CN is 'glab'.

    def cn (self): return 'glab'

    ##  ID is USER/NAME.

    def id (self):
        nb = self.file
        user = self.file.parent().name()
        return user + '/' + nb.name()

    ##  Write a block of 'N' records.

    def com_export (self, stream):
        nb = self.file
        self.start_block(stream)
        for line in nb.output_lines():
            if '\t' in line:
                raise Exception('Tab in output line')
            stream.write_record('N', line)

    ##  Read a block of 'N' records.

    def com_import (self, stream):
        nb = self.file
        nb._title = None
        nb._texts = []
        with writer(nb):
            for rec in stream.restrict_to('N'):
                line = rec[1]
                if nb._title is None:
                    if line.startswith('#T '): line = line[3:]
                    nb._title = line
                else:
                    nb.append_text(line)
        if nb._title is None:
            nb._title = 'Untitled'
