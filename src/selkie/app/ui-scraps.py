
#  /foo is a directory, /foo/ is its home page.
#  Exclude home pages.
#  Roots and home pages have empty names.  But a home page has a parent.

def _ancestors (item):
    if isinstance(item, UIObject):
        for anc in _ancestors(item.__parent__):
            yield anc
        if isinstance(item, Requestable):
            yield item

def Path (page, root='Top'):
    path = BasicElement(page, 'div', block=True, htmlclass='path')
    items = list(_ancestors(page))
    last = len(items) - 1

    for i in range(len(items)):
        item = items[i]
        if i == 0: name = root
        else: name = item.__upc__.name
        pathname = item.__upc__.pathname
        if isinstance(item, HtmlDirectory):
            pathname += '/'
        if i == last:
            String(path, name)
        else:
            Link(path, name, pathname)
            String(path, ' > ')
    return path
