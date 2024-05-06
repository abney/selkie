##  \package seal.script.doc
#   Generate documentation from comments.  I stopped development on this
#   in favor of using doxygen.
#
#   The main function takes a module name (e.g., 'seal.cld'), imports it,
#   and calls write_documentation(module).

import os
from os import listdir
from os.path import join, isdir, exists
from importlib import import_module
from inspect import getmembers, isclass, isfunction, signature, getmro, \
    getsourcelines, getfile, getcomments

from seal.core import sh
from seal.core.misc import shift


##  The beginning of the HTML output.
file_hdr = '''<html>
<head>
<title>%s</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<link rel="stylesheet" type="text/css" href="%sdefault.css"/>
</head>
<body>
<h1>%s</h1>
'''

##  Link to TOC, inserted at the beginning of the body.
file_toplink = '''<p class="nav"><a href="%sindex.html">API</a></p>
'''

##  The end (footer) of the HTML output.
file_ftr = '''</body>
</html>
'''


def _is_oblig (p):
    return ((p.kind == p.POSITIONAL_ONLY or p.kind == p.POSITIONAL_OR_KEYWORD) and
            p.default == p.empty)

##  Pretty-printed argument list.

def pretty_arglist (f, ismethod):
    words = ['(']
    sig = signature(f)
    params = list(sig.parameters.values())
    if ismethod: start = 1
    else: start = 0
    optional = False
    for i in range(start, len(params)):
        p = params[i]
        if i > start:
            words.append(', ')
        if not (optional or _is_oblig(p)):
            words.append('[')
            optional = True
        if p.kind == p.VAR_POSITIONAL:
            words.append('*')
        elif p.kind == p.VAR_KEYWORD:
            words.append('**')
        words.append('<i>')
        words.append(p.name)
        words.append('</i>')
    if optional:
        words.append(']')
    words.append(')')
    return ''.join(words)

##  Print function declaration.

def function_header (f, ismethod):
    return '<dt id="%s"><tt>%s%s</tt></dt>' % (f.__name__, f.__name__, pretty_arglist(f, ismethod))

##  Print function description.

def function_body (f):
    return '<dd>%s</dd>' % (getdoc(f) or '')

##  Get the list of class instance variables.

def class_instance_variables (c):
    init = c.__dict__.get('__init__')
    if init is None:
        return []
    (lines, _) = getsourcelines(init)
    table = {}

    prev = ''
    for line in lines:
        line = line.strip()
        n = line.find('=')
        if n >= 0:
            var = line[:n].strip()
            if var.startswith('self.'):
                if prev.startswith('#'):
                    doc = prev.strip('# ')
                else:
                    doc = ''
                var = var[5:]
                if ispublic(var):
                    if var in table:
                        oldval = table[var]
                        if oldval and doc:
                            table[var] = oldval + '\n' + doc
                        else:
                            table[var] = oldval + doc
                    else:
                        table[var] = doc
        prev = line

    return sorted(table.items())

##  Interesting parents.

def interesting_parents (c):
    for parent in getmro(c):
        if not (parent is c or parent is object):
            yield c

def _n_leading_spaces (line):
    i = 0
    while i < len(line) and line[i].isspace():
        i += 1
    return i

##  Clean up a documentation string.

def clean_docstring (s):
    lines = s.split('\n')
    if len(lines) == 1:
        return s
    ind = _n_leading_spaces(lines[1])
    if ind == 0:
        return s
    lines[1] = lines[1][ind:]
    for i in range(2, len(lines)):
        n = _n_leading_spaces(lines[i])
        if n > 0:
            if n > ind: n = ind
            lines[i] = lines[i][n:]
    return '\n'.join(lines)
        
def _eol (s, i, n):
    j = s.find('\n', i)
    if j < 0:
        return n
    else:
        return j + 1

def _skip_hashes (s, i, j):
    while i < j and s[i] == '#':
        i += 1
    return i

def _skip_spaces (s, i, j):
    while i < j and s[i].isspace():
        i += 1
    return i

##  Clean up a comment block.

def clean_comments (s):
    i = 0
    n = len(s)
    indent = None
    lines = []
    while i < len(s):
        j = _eol(s, i, n)
        i = _skip_hashes(s, i, j)
        k = _skip_spaces(s, i, j)
        nsp = k - i
        if indent is None:
            indent = nsp
            i = k
        elif nsp > indent:
            i += indent
        else:
            i = k
        lines.append(s[i:j])
        i = j+1
    lines.append('')
    return ''.join(lines)

##  Get documentation for something.

def getdoc (x):
    doc = getcomments(x)
    if doc:
        return clean_comments(doc)
    else:
        return ''

##  Whether the name is public.  It is private if it starts with an underscore
#   but is not of form __xxx__.

def ispublic (name):
    return ((not name.startswith('_')) or
            (name.startswith('__') and name.endswith('__')))


##  The toplevel call.  The argument is a module, which may represent itself
#  or may represent a package.  To be precise, it represents a package if its
#  filename ends with /__init__.py, but its name does <i>not</i> end with
#  .__init__.
#
#  If the module represents a package, a DocDir is created and saved.
#  Otherwise, a ModuleFile is created and saved.

def write_documentation (module):
    name = module.__name__
    fn = module.__file__
    # package
    if fn.endswith('/__init__.py') and not name.endswith('.__init__'):
        DocDir(module).save()
    else:
        ModuleFile(module).save()


##  Documentation directory.

class DocDir (object):

    ##  Constructor.

    def __init__ (self, module):

        ##  Module name.
        self.name = module.__name__

        ##  The directory.
        self.dir = module.__file__[:-12]

        ##  Qualified names.
        self.packages = None

        ##  Qualified names.
        self.modules = None

        ##  Classes, functions.
        self.objects = None

    ##  Save it.

    def save (self):
        self.packages = []
        self.modules = []
        self.objects = []
        self._save_recurse(self.name, self.dir)
        self._write_toc()

    def _save_recurse (self, qualname, dir):
        self.packages.append(qualname)
        for name in listdir(dir):
            if name.endswith('.disabled'):
                continue
            elif name.endswith('.py'):
                modqualname = qualname + '.' + name[:-3]
                try:
                    m = import_module(modqualname)
                    self.modules.append(modqualname)
                    ModuleFile(m).save(updating=self)
                except ModuleNotFoundError:
                    print('** Module %s not found, while processing dir %s' % (modqualname, dir))
            else:
                subdir = join(dir, name)
                if isdir(subdir) and exists(join(subdir, '__init__.py')):
                    self._save_recurse(qualname + '.' + name, subdir)

    def _write_toc (self):
        print('Writing index.html')
        with open('index.html', 'w') as f:
            name = self.name.replace('.', '/')
            f.write(file_hdr % (name, '', name))

            if self.packages:
                f.write('<h2>Packages</h2>\n')
                f.write('<ul>\n')
                for name in sorted(self.packages):
                    f.write('<li><a href="%s/__init__.html">%s</a></li>\n'
                            % (name.replace('.', '/'), name))
                f.write('</ul>\n')

            if self.modules:
                f.write('<h2>Modules</h2>\n')
                f.write('<ul>\n')
                for name in sorted(self.modules):
                    if name.endswith('.__init__'):
                        pretty_name = name[:-9]
                    else:
                        pretty_name = name
                    f.write('<li><a href="%s.html">%s</a></li>\n'
                            % (name.replace('.', '/'), pretty_name))
                f.write('</ul>\n')

            if self.objects:
                f.write('<h2>Objects</h2>\n')
                f.write('<ul>\n')
                for obj in sorted(self.objects, key=lambda o:o.__name__):
                    fn = obj.__module__.replace('.', '/')
                    f.write('<li><a href="%s.html#%s">%s</a> (%s)</li>\n'
                            % (fn, obj.__name__, obj.__name__, obj.__module__))
                f.write('</ul>\n')
    
            f.write(file_ftr)


##  Represents a .py source file.

class ModuleFile (object):

    ##  Constructor.

    def __init__ (self, module):

        ##  The module.
        self.module = module

        ##  The pathname, as a list of components.
        self.cpts = module.__name__.split('.')
        if len(self.cpts) < 2:
            raise Exception('Expecting nested module name')

        ##  The filename of the html file.
        self.filename = '/'.join(self.cpts) + '.html'

        ##  The open stream.
        self.file = None

        ##  Updating flag.
        self.updating = None
    
    ##  Save it.

    def save (self, updating=None):
        self.updating = updating
        dir = os.path.dirname(self.filename)
        if not os.path.exists(dir):
            os.makedirs(dir)
        css_src = os.path.expanduser('~/git/seal/data/seal/default.css')
        cssfn = 'default.css'
        if not os.path.exists(cssfn):
            print('Writing', cssfn)
            sh.cp(css_src, cssfn)
        print('Writing', self.filename)
        with open(self.filename, 'w') as self.file:
            self.write_header()
            self.write_module_doc()
            self.write_function_section()
            for c in self.public_classes():
                self.write_class_section(c)
            self.write_footer()
        self.updating = None

    ##  Write the header.

    def write_header (self):
        name = self.module.__name__
        up = '/'.join('..' for _ in range(len(self.cpts)-1))
        if up: up = up + '/'
        self.file.write(file_hdr % (name, up, name))
        self.file.write(file_toplink % up)
        self.file.write('\n')

    ##  Write the footer.

    def write_footer (self):
        self.file.write('</body>\n')
        self.file.write('</html>\n')

    ##  Write documentation for my module.

    def write_module_doc (self):
        doc = getdoc(self.module)
        if doc:
            self.file.write(doc)

    ##  Write documentation for the functions.

    def write_function_section (self):
        self._write_function_section1(self.module, '<h2>Functions</h2>')

    ##  Write documentation for the methods.

    def write_method_section (self, c):
        self._write_function_section1(c, '<h3>Methods</h3>', True)

    ##  List of public functions.

    def public_functions (self, obj):
        for (_,f) in getmembers(obj, isfunction):
            # getfile signals an error if the object is builtin
            try:
                if getfile(f) == self.module.__file__ and ispublic(f.__name__):
                    yield f
            except:
                pass

    ##  List of public classes.

    def public_classes (self):
        for (_,f) in getmembers(self.module, isclass):
            # getfile signals an error if the object is builtin
            try:
                if getfile(f) == self.module.__file__ and ispublic(f.__name__):
                    yield f
            except:
                pass

    def _write_function_section1 (self, obj, title, ismethod=False):
        functions = list(self.public_functions(obj))
        if functions:
            self.file.write(title)
            self.file.write('\n')
            self.file.write('<dl>\n')
            for f in functions:
                if self.updating is not None:
                    self.updating.objects.append(f)
                self.file.write(function_header(f, ismethod))
                self.file.write('\n')
                self.file.write(function_body(f))
                self.file.write('\n')
            self.file.write('</dl>\n')
    
    ##  The relative pathname of a module.

    def module_relpath (self, m):
        cpts1 = m.split('.')
        n = 0
        while n < min(len(cpts1), len(self.cpts)) and cpts1[n] == self.cpts[n]:
            n += 1
        cpts = ['..' for _ in range(len(self.cpts) - n)] + cpts1[n:]
        return '/'.join(cpts)

    ##  The documentation file for a class.

    def class_filename (self, c):
        mp = self.module_relpath(c.__module__)
        if mp:
            return mp + '/' + c.__name__ + '.html'
        else:
            return c.__name__ + '.html'
        
    ##  A link to the documentation file.

    def class_link (self, c):
        return '<a href="%s">%s</a>' % (self.class_filename(c), c.__name__)

    ##  Write documentation for a class.

    def write_class_section (self, c):
        if self.updating is not None:
            self.updating.objects.append(c)
        self.file.write('<h2 id="%s"><i>class</i> %s</h2>\n' % (c.__name__, c.__name__))
        self.write_parent_par(c)
        self.write_class_doc(c)
        self.write_member_section(c)
        self.write_method_section(c)

    ##  Write the list of classes that this class inherits from.

    def write_parent_par (self, c):
        pars = list(interesting_parents(c))
        if pars:
            self.file.write('<p>\n')
            self.file.write('Specializes: ')
            self.file.write(' '.join(self.class_link(p) for p in pars))
            self.file.write('</p>\n')

    ##  Write the documentation string for the class.

    def write_class_doc (self, c):
        doc = getdoc(c)
        if doc:
            self.file.write(doc)
            self.file.write('\n')

    ##  Write the list of instance variables.

    def write_member_section (self, c):
        vbls = class_instance_variables(c)
        if vbls:
            self.file.write('<h3>Members</h3>\n')
            self.file.write('<dl>\n')
            for (vbl, doc) in vbls:
                if self.updating is not None:
                    self.updating.objects.append(ClassVariable(c, vbl))
                self.file.write('<dt><tt>%s</tt></dt>\n' % vbl)
                self.file.write('<dd>')
                self.file.write(doc)
                self.file.write('</dd>\n')
            self.file.write('</dl>\n')


##  A class variable.

class ClassVariable (object):

    ##  Constructor.

    def __init__ (self, cls, vbl):

        ##  Qualified name.
        self.__module__ = cls.__module__ + '.' + cls.__name__

        ##  The variable.
        self.__name__ = vbl

##  Main function.

def main ():
    name = shift()
    shift.done()
    module = import_module(name)
    write_documentation(module)

if __name__ == '__main__':
    main()
