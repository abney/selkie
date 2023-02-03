##  \package seal.script.dependencies
#   Computing dependencies among modules.

from os import listdir
from os.path import join, isdir, exists
from importlib import import_module
from seal.core.io import pprint
from seal.core.misc import shift

##  Module.__name__ and module.__package__ are both qualified names (strings
#   containing dots).  If the module is itself a package, they are the same.

def is_package (module):
    return module.__name__ == module.__package__

##  A package has __name__ 'foo.bar' but __file__ '.../foo/bar/__init__.py'
#   The return value is an absolute pathname.

def module_filename (module):
    if is_package(module):
        # strip '/__init__.py'
        return module.__file__[:-12]
    else:
        return module.__file__

##  Parent must be a package; name must be a string.
#   Return value is a module.

def module_child (parent, name):
    return import_module(parent.__name__ + '.' + name)


##  Returns a preorder iteration over the modules contained in the given
#   root module, which may be either a package or a terminal module.

def modules (module):
    for item in _modules_and_strays(module):
        if not isinstance(item, str):
            yield item

##  Returns a preorder iteration over stray files.  These are the absolute
#   pathnames of all files that are encountered but not included in the
#   iteration over modules.

def stray_files (module):
    for item in _modules_and_strays(module):
        if isinstance(item, str):
            yield item

def _ignore (name):
    return (name.endswith('.disabled') or
            name.endswith('.todelete') or
            name.endswith('.safe') or
            name.endswith('-scraps') or
            name.endswith('_scraps') or
            name.endswith('-scraps.py') or
            name.endswith('_scraps.py') or
            name.endswith('~') or
            name.endswith('__') or
            name.startswith('#') or
            name.startswith('tmp.') or
            name == 'tmp')

def _modules_and_strays (module):
    if isinstance(module, str):
        module = import_module(module)
    todo = [module]
    while todo:
        module = todo.pop()
        if is_package(module):
            modfn = module_filename(module)
            for name in reversed(listdir(modfn)):
                fn = join(modfn, name)
                if _ignore(name):
                    yield fn
                elif name.endswith('.py'):
                    todo.append(module_child(module, name[:-3]))
                elif isdir(fn) and exists(join(fn, '__init__.py')):
                    try:
                        todo.append(module_child(module, name))
                    except:
                        print('ERROR: Got an error importing %s.%s' % (module.__name__, name))
                else:
                    yield fn
        else:
            yield module

def _add_deps (fields, deps, parent):
    n = len(fields)
    continuation = False
    if fields[-1] == '\\':
        n -= 1
        continuation = True
    for i in range(n):
        name = fields[i]
        if name == 'as':
            break
        if name.endswith(','): name = name[:-1]
        # check that it is legit
        try:
            import_module(name)
            deps.add(name)
        except:
            print('ERROR: in %s: got an error trying to import %s' % (parent.__name__, name))
    return continuation

##  Returns a table of dependencies.

def dependencies (root_module):
    table = {}
    for module in modules(root_module):
        deps = set()
        name = module.__name__
        if name.endswith('.__init__'): name = name[:-9]
        table[name] = deps
        continuation = False
        with open(module.__file__) as f:
            for line in f:
                line = line.strip()
                if (not line) or line.startswith('#'):
                    continue
                fields = line.split()
                if continuation:
                    continuation = _add_deps(fields, deps, module)
                elif fields[0] == 'import' and len(fields) > 1:
                    continuation = _add_deps(fields[1:], deps, module)
                elif fields[0] == 'from' and len(fields) > 3 and fields[2] == 'import':
                    _add_deps(fields[1:2], deps, module)
                    continuation = False
                else:
                    continuation = False
    return table

# #
# #  Return value will not have a value for all keys, if there is a cycle
# #
# def _compute_depths (table):
#     depths = {}
#     todo = list(table)
#     progress = True
#     while todo and progress:
#         doing = todo
#         todo = []
#         progress = False
#         while doing:
#             key = doing.pop()
#             d = _compute_depth(key, table, depths)
#             if d is None:
#                 todo.append(key)
#             else:
#                 depths[key] = d
#                 progress = True
#     return depths
# 
# def _compute_depth (key, table, depths):
#     # max depth for any module key depends on
#     maxd = -1
#     for value in table[key]:
#         # ignore system modules
#         if value in table:
#             d = depths.get(value)
#             if d is None:
#                 # depth cannot be computed yet
#                 return None
#             elif d > maxd:
#                 maxd = d
#     return maxd + 1


##  The dependencies for a particular module.

class Dependencies (object):

    ##  Constructor.

    def __init__ (self, module):

        ##  The module whose dependencies these are.
        self.module = module

        ##  The dependencies.
        self.dependencies = dependencies(module)

        ##  Reverse dependencies: modules that import this one.
        self.rev_dependencies = None

        ##  Module that imports nothing else has height 0.
        self.heights = None

        ##  Modules indexed by height.
        self.by_height = None

        ##  A proxy is the representative for the equivalence class introduced
        #   by a cycle.
        self.proxies = None

        ##  Cycles.
        self.cycles = None

    ##  True if the name is not in my list of dependencies.

    def is_system_module (self, name):
        return name not in self.dependencies

    def _compute_heights (self):
        self.heights = {}
        self.proxies = {}
        for node in self.dependencies:
            if not (node in self.heights or node in self.proxies):
                self._compute_height(node, tuple())

    def _compute_height (self, node, ancs):
        heights = self.heights
        children = self.dependencies

        # possibly proxy == node
        proxy = self.get_proxy(node)
        if proxy in heights:
            #pprint(node, '->', heights[proxy])
            return heights[proxy]

        elif self._detect_cycle(node, proxy, ancs):
            #pprint(node, 'CYCLE detected', -1)
            return -1

        else:
            #pprint(node)
            maxh = -1
            ancs = ancs + (node,)

            # with pprint.indent(): # **
    
            for child in children[node]:
                if not self.is_system_module(child):
                    h = self._compute_height(child, ancs)
                    if h > maxh: maxh = h
        
            if node in self.proxies:
                #pprint('(%s)' % maxh)
                return maxh
            else:
                assert node not in heights
                heights[node] = maxh + 1
                #pprint('->', maxh + 1)
                return maxh + 1

    ##  May need to chase proxy links.  The node returned has no proxy.

    def get_proxy (self, node):
        while node in self.proxies:
            node = self.proxies[node]
        return node


    #  if proxy != node, proxy must be in ancs
    #  if proxy == node, maybe not

    def _detect_cycle (self, node, proxy, ancs):
        i = 0
        while i < len(ancs) and ancs[i] != proxy:
            i += 1
        
        if i < len(ancs):
            assert proxy not in self.proxies
            for j in range(i+1, len(ancs)):
                self.proxies[ancs[j]] = proxy
            return True

        else:
            assert node == proxy
            return False

    def _invert_heights (self):
        heights = self.heights
        self.by_height = out = {}
        for (name, h) in heights.items():
            if h in out:
                out[h].append(name)
            else:
                out[h] = [name]
    
    def _invert_proxies (self):
        proxies = self.proxies
        self.cycles = cycles = {}
        for node in proxies:
            proxy = self.get_proxy(node)
            if proxy in self.cycles:
                self.cycles[proxy].append(node)
            else:
                self.cycles[proxy] = [node]

            
    ##  The main entry point.  Prints dependencies sorted by their
    #   'heights'.  The height computation goes as follows.
    #
    #   A module's 'children' are the modules that it depends on.
    #   Make recursive calls to compute height.
    #   My height is my max child height, plus one.
    #
    #   While a node's height is being computed, it resides on the
    #   ancestor list.  I.e., no node on the ancestor list has a height yet.
    #
    #   If a node N is on the ancestor list, all the nodes from N
    #   down on the ancestor list belong to a cycle.  The highest node
    #   on the ancestor list becomes the proxy, and all others become
    #   'elided nodes'.
    #
    #   It is possible that some of the nodes in the cycle already have
    #   a proxy.  Then we have detected a larger cycle that subsumes the
    #   known cycle.  Redirect the old proxy to the new proxy.
    #   Redirecting the other proxies as well does no harm; it saves
    #   a step in chasing proxy links.
    #
    #   If we encounter a node that has a known height (chasing proxy
    #   links, if any), immediately return the known height.
    #
    #   If the height is not known, but there is a proxy, that proxy must
    #   still be on the ancestor list.  Skip this node - i.e., return -1.
    #  
    #   Otherwise, make a pass through the (non-system) children, computing
    #   the max height.  It is possible that my proxy will get set in the
    #   process.  At the end, return the max height, if my proxy got set.
    #   Otherwise, set my height to the max child height plus one, and
    #   return it.
    #
    #   Note that elided nodes never have their height set.

    def com_show (self):
        self._compute_heights()
        self._invert_heights()
        self._invert_proxies()

        if self.cycles:
            pprint('Cycles:')
            with pprint.indent():
                for (proxy, lst) in self.cycles.items():
                    pprint(proxy, *lst)
                
        for (h, nodes) in sorted(self.by_height.items()):
            pprint()
            pprint('Generation %d:' % h)
            with pprint.indent():
                for node in nodes:
                    pprint(node, self._height_str(node))
                    with pprint.indent():
                        for dep in sorted(self.dependencies[node]):
                            pprint(dep, self._height_str(dep))

    def _height_str (self, node):
        if self.is_system_module(node):
            return ''
        elif node in self.proxies:
            proxy = self.get_proxy(node)
            return '-> %s %d' % (proxy, self.heights[proxy])
        else:
            return str(self.heights[node])

    def _invert_dependencies (self):
        self.rev_dependencies = revtab = {}
        for (node, deps) in self.dependencies.items():
            for dep in deps:
                if dep in revtab:
                    revtab[dep].append(node)
                else:
                    revtab[dep] = [node]
        
    ##  Print out the list of modules that depend on me.

    def com_reverse (self):
        self._invert_dependencies()

        for (node, deps) in sorted(self.rev_dependencies.items()):
            pprint(node)
            with pprint.indent():
                for dep in deps:
                    pprint(dep)

##  The main function.
#   Takes a module name and prints everything it depends on.
#   Optionally accepts the flag -r, meaning to print the modules that
#   depend on the named one.

def main ():
    com = 'com_show'

    if shift.isflag():
        flag = shift()
        if flag == '-r':
            com = 'com_reverse'

    root_module = shift()
    shift.done()

    getattr(Dependencies(root_module), com)()


if __name__ == '__main__':
    main()
