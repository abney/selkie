
from asyncio import ensure_future
from pathlib import Path
from ..corpus import (Registry, Corpus, Node, Language, Toc, Text, Sents, Sentence, Props, Roms, Rom)
from ..wap import Element, EditableCell


class Location:
        
    node_types = ('corp', 'lang', 'text', 'sent', 'form')
    NNodes = 5

    def __init__ (self):
        self.node = None
        self.item = None
        self.nodes = [None] * self.NNodes

    def corpus (self): return self.nodes[0]
    def language (self): return self.nodes[1]
    def text (self): return self.nodes[2]
    def sentence (self): return self.nodes[3]
    def form (self): return self.nodes[4]

#     def _compute_nodes (self, oldloc):
#         node = self.node
#         if oldloc is None:
#             if node is None:
#                 return [None] * self.NNodes
#             else:
#                 return list(node.ancestors())
#         else:
#             nodes = list(oldloc.nodes)
#             if node is not None:
#                 ancs = list(node.ancestors())
#                 lvl = node.level()
#                 # if this is a new node, clear old-node descendants
#                 if nodes[lvl] != node:
#                     for i in range(lvl+1, self.NNodes):
#                         nodes[i] = None
#                 while lvl >= 0 and node is not None and nodes[lvl] != node:
#                     nodes[lvl] = node
#                     node = node.parent
#                     lvl -= 1
#             return nodes

    def __repr__ (self):
        return f"<Location {' '.join(node.key for node in self.nodes if node is not None)}>"


class EditorElement (Element):

    def PlainTextPanel (self, text, **kwargs):
        return self.create(PlainTextPanel, text, **kwargs)


class State:

    def __init__ (self, node):
        self.child = None
        self.item = node.views()[0]

    def __repr__ (self):
        child = None if self.child is None else self.child.full_name
        item = None if self.item is None else self.item.full_name
        return f'<State item={repr(item)} child={repr(child)}>'


class Editor (EditorElement):

    def __init__ (self, server):
        EditorElement.__init__(self, None, None)
        self.server = server
        self.selected = None
        self.registry = Registry()

        self.edit(self.registry)

    def corpus (self): return self.selected.corpus()
    def language (self): return self.selected.language()
    def text (self): return self.selected.text()
    def sentence (self): return self.selected.sentence()
    def form (self): return self.selected.form()

    def edit (self, item):
        self.selected = item
        item.select()
        view = item.current_view
        self.goto_page(view.Page, view)

#     def update_location (self, item):
#         if isinstance(item, Node):
#             node = item
#             item = self.intern_state(node).item
#         else:
#             node = item.node()
#         self.store_state(node, item)
#         self.location.item = item
#         self.location.node = node
#         nodes = self.location.nodes
#         i = 0
#         nodes[i] = self.intern_state(self.corpora).child
#         while nodes[i] is not None and i+1 < len(nodes):
#             nodes[i+1] = self.intern_state(nodes[i]).child
#             i += 1
# 
#     def store_state (self, node, item):
#         self.intern_state(node).item = item
#         nodes = list(node.ancestors())
#         if nodes:
#             self.intern_state(self.directory).child = nodes[0]
#             for i in range(len(nodes)-1):
#                 self.intern_state(nodes[i]).child = nodes[i+1]
# 
#     def intern_state (self, node):
#         key = node.full_name
#         if key in self.state_table:
#             return self.state_table[key]
#         else:
#             state = State(node)
#             self.state_table[key] = state
#             return state

#     def current_view (self, node):
#         if node.full_name in self.current_view_table:
#             return self.current_view_table[node.full_name]
#         else:
#             return node.views()[0]
# 
#     def set_current_view (self, node, item):
#         self.current_view_table[node.full_name] = item

#     def update_location (self, item):
#         if isinstance(item, Node):
#             node = item
#             item = self.current_view(node)
#         else:
#             node = item.node()
#         self.location = Location(node, item, self.location)
#         node = self.location.node
#         if node is not None:
#             self.set_current_view(node, self.location.item)
#         if isinstance(node, Corpus):
#             if node.key not in self.corpus_table:
#                 self.corpus_table[node.key] = node
#         return item

    def goto_page (self, cls, item):
        self.clear()
        self.create(cls, item)

    def open_corpus (self, fn):
        doc = self.document
        doc.clear()
        doc.write('Opening corpus', fn, '...')
        ensure_future(self._open_corpus(fn))

    async def _open_corpus (self, fn):
        if isinstance(fn, str):
            contents = await self.server.load(fn)
        else:
            contents = fn.contents
            fn = fn.name
        self.edit(self.registry.open(fn, contents=contents))

    def create_corpus (self):
        self.edit(self.registry.new())

    ## new - the '+' entries in the menus

#     def choose_file (self):
#         self.edit(CorpusChooser())

    def new_corp (self, *args):
        self.edit(self.registry)

    def new_lang (self):
        pass

    def new_text (self):
        pass

    def new_sent (self):
        pass

    def new_form (self):
        pass

    def new_rom (self):
        print('** new_rom: unimplemented')

    ## edit

    def edit_corp (self, key):
        self.edit(self.registry.get(key))

#     def edit_language (self, name):
#         lang = self.location.corpus.table[name]
#         self.edit(lang)

    def edit_lang (self, nid):
        lang = self.corpus().language(nid)
        self.edit(lang)

    def edit_text (self, name):
        text = self.language().texts[name]
        self.edit(text)
        
    def edit_sent (self, name):
        pass

    def edit_form (self, name):
        pass

    def edit_rom (self, name):
        pass


#--  Mid-level components  -----------------------------------------------------

class SentenceCell (EditableCell):

    def __init__ (self, parent, sent, **kwargs):
        EditableCell.__init__(self, parent, sent.string, sent.set_string, **kwargs)


class PlainTextPanel (EditorElement):

    def __init__ (self, parent, sents):
        Element.__init__(self, parent, 'div')
        assert isinstance(sents, Sents)
        self.sents = sents
        self.table = self.Table(classname='grid')

        for sent in sents:
            row = self.table.Row()
            row.create(SentenceCell, sent)


# class PropertyCell (EditableCell):
# 
#     def __init__ (self, parent, meta, key):
#         # EditableCell.__init__ is going to call self.get in order to display itself
#         self.meta = meta
#         self.key = key
#         EditableCell.__init__(self, parent, self.get, self.set, classname='editable')
# 
#     def get (self):
#         return self.meta[self.key]
# 
#     def set (self, value):
#         self.meta[self.key] = value
#     
# 
# class PropertyTable (EditorElement):
# 
#     def __init__ (self, parent, meta):
#         Element.__init__(self, parent, 'table', classname='noborder')
#         self.meta = meta
# 
#         for (key, value) in self.meta.items():
#             if not isinstance(value, dict):
#                 row = self.Row()
#                 cell = row.TD()
#                 cell.write(key)
#                 row.create(PropertyCell, self.meta, key)

        
#--  Pages  --------------------------------------------------------------------

class Page (EditorElement):

    def __init__ (self, editor, item):
        Element.__init__(self, editor, 'div')
        self.editor = editor
        self.item = item


class StandardPage (Page):

    def __init__ (self, editor, item):
        Page.__init__(self, editor, item)
        self.construct_menu()
        self.construct_title()

    def construct_menu (self):
        editor = self.editor
        menubar = self.document.MenuBar()

        for lst in editor.selected.current():
            nodetype = lst.ElementType.Choice
            selected = lst.selected
            editfun = getattr(editor, 'edit_' + nodetype)
            newfun = getattr(editor, 'new_' + nodetype)
            if selected is None:
                menu = menubar.Menu(f'({nodetype})')
            else:
                menu = menubar.Menu(selected.nid, editfun, selected.nid)
            for alt in lst:
                if alt is not selected:
                    menu.MenuItem(alt.nid, editfun, alt.nid)
            menu.MenuItem('+', newfun)

#     def construct_menu_safe (self):
#         editor = self.editor
#         loc = editor.location
#         menubar = self.document.MenuBar()
#         views = []
# 
#         if loc.corpus is None:
# 
#             menu = menubar.Menu('open')
# 
#         else:
# 
#             menu = menubar.Menu(loc.corpus.key, editor.edit_corpus)
#             menu.MenuItem('+', editor.choose_file)
# 
# #            views.append('corp')
# 
#             title = 'Langs'
#             if loc.language is not None:
#                 title = loc.language.key
#                 views.append('lang')
#             menu = menubar.Menu(title, editor.edit_language, title)
#             for name in loc.corpus.table:
#                 if name != title:
#                     menu.MenuItem(name, editor.edit_language, name)
# 
#             title = 'Texts'
#             if loc.text is not None:
#                 title = loc.text.key
#                 views.append('text')
#             menu = menubar.Menu(title, editor.edit_text, title)
#             if loc.language:
#                 for name in loc.language.table:
#                     if name != title:
#                         menu.MenuItem(name, editor.edit_text, name)

#         view = loc.view
#         menu = menubar.Menu(view)
# 
#         for alt in views:
#             if alt != view:
#                 menu.MenuItem(alt, self.goto_page, alt)

    def construct_title (self):
        editor = self.editor
        selected_view = editor.selected.current_view
        node = selected_view.view_of
        h2 = self.H2()
        h2.write(node.display_string())
        if node.views and len(node.views) > 1:
            h2.write(' : ')
            for view in node.views:
                button = h2.Button(view.view_name(), (editor.edit, view))
                button.style.marginLeft = '5px'
                if view is selected_view:
                    button.disable()

    def goto_view (self, cls):
        editor = self.editor
        node = editor.location.node
        if isinstance(node, cls):
            item = node
        else:
            item = cls(node)
        editor.edit(item)


class RegistryPage (StandardPage):

    def __init__ (self, editor, item):
        StandardPage.__init__(self, editor, item)
        self.box = None
        self.div = div = self.Div()
        self.listing = div.UL()
        ul = div.UL()
        ul.LI().Button('+ new corpus', self.editor.create_corpus)
        if editor.server is not None:
            p = ul.LI().P()
            p.write('Open file: ')
            self.box = p.TextEntry(submit=self.editor.open_corpus)
            p.write(' ')
            p.Upload(action=editor.open_corpus)
        ensure_future(self.list_dir())

    async def list_dir (self):
        ul = self.listing
        server = self.editor.server
        if server is not None:
            text = await server.list_dir()
            lst = [fn for fn in text.split('\n') if fn.endswith('.cld')]
            for fn in lst:
                ul.LI().Button(fn, (self.editor.open_corpus, fn))
        self.box.focus()


class CorpusPage (StandardPage):

    def __init__ (self, editor, corpus):
        StandardPage.__init__(self, editor, corpus)
        self.corpus = corpus
        self.table = {'filename': corpus.filename()}
        self.DictEditor(self.table, self.property_change)
        p = self.P()
        button = p.Button()
        button.write('Download')
        button.add_listener('click', self.download)

    def property_change (self, key, value):
        if key == 'filename':
            self.editor.directory.rename(self.corpus, value)
            self.editor.edit(self.corpus)

    def download (self, evt):
        corpus = self.item
        self.download_file(corpus.filename(), corpus.export_cld())


class PropsPage (StandardPage):

    def __init__ (self, editor, props):
        StandardPage.__init__(self, editor, props)
        self.DictEditor(props)
        p = self.P()


class TocPage (StandardPage):

    def __init__ (self, editor, toc):
        StandardPage.__init__(self, editor, toc)
        self._produce_ul(self, toc.roots())

    def _produce_ul (self, parent, texts):
        ul = parent.UL()
        for text in texts:
            li = ul.LI()
            li.Button(text=f'[{text.nid}] {text.title()}', action=(self.editor.edit, text))
            children = text.children()
            if children:
                self._produce_ul(li, children)


class SentsPage (StandardPage):

    def __init__ (self, editor, text):
        StandardPage.__init__(self, editor, text)
        self.PlainTextPanel(text)
        

class IGTPage (StandardPage):

    def __init__ (self, editor, igt):
        StandardPage.__init__(self, editor, igt)
        

class RomsPage (StandardPage):

    def __init__ (self, editor, roms):
        StandardPage.__init__(self, editor, roms)
        ul = self.UL()
        for rom in roms:
            ul.LI().Button(text=name, action=(self.editor.edit, rom.nid))
        ul.LI().Button(text='+ rom', action=self.editor.new_rom)


#--  Node updates  -------------------------------------------------------------

Registry.Page = RegistryPage
Corpus.Page = CorpusPage
Props.Page = PropsPage
Toc.Page = TocPage
Roms.Page = RomsPage
Sents.Page = SentsPage
