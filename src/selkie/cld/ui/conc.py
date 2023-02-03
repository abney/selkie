##  @package seal.cld.ui.conc
#   Concordance.

from seal.app.html import *


#--  Concordance  --------------------------------------------------------------

##  Add a highlighting page element.

def highlighting (parent, lexent, par, rom):
    first = True
    for token in par:
        if first: first = False
        else: String(parent, ' ')
        s = rom.decode(str(token))
        if token._lexent is lexent:
            Span(parent, s, htmlclass='tokenSelected')
        else:
            String(parent, s)

##  Create a concordance page.

def concordance (parent, lexicon, lxid):
    lang = lexicon.language()
    lexent = lexicon.by_index(int(lxid))
    title = 'Concordance: %s.%d' % lexent.key()
    page = HtmlPage(parent, title=title)
    PathWithLogin(page)
    menu = MenuBar(page)
    Button(menu, '<<', '../')
    H1(page, title)
    table = Table(page, htmlclass='ParallelText')
    default_rom = parent.file.env.require_rom('default')
    for par in lexent.paragraphs():
        textid = par.textid()
        text = lang.get_text(textid)
        if text.permitted('read'):
            url = parent.context.root.text_url(text)
            value = '%s/page/igt.%d/edit' % (url, par.index())
        else:
            value = 'null'
        rom = par.romanization()
        row = Row(table)
        cell = Cell(row)
        p = P(cell, htmlclass='textpar')
        p.set_attribute('data-value', value)
        highlighting(p, lexent, par, rom)
        cell = Cell(row)
        p = P(cell, htmlclass='textpar')
        p.set_attribute('data-value', value)
        String(p, default_rom.decode(par.translation()))
    page.add_stylesheet('conc')
    page.add_import('conc')
    return page
