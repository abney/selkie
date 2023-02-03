##  @package seal.app.weblib
#   JS and CSS scripts.
#   Implements 'import'.

import os
from seal.core.io import data, split_suffix


##  A table of scripts.

class Scripts (object):

    ##  Create one from a directory.

    def __init__ (self, dir=None):
        if dir is None: dir = data.seal

        ##  The directory.
        self.dir = dir

        ##  The table.
        self.table = {}

    ##  Intern a key in the table.  If the key is already in the table,
    #   the value is returned, otherwise a new Script is created.
    #   The key is a pair that is passed to the Script constructor.

    def intern (self, key):
        if key in self.table:
            return self.table[key]
        else:
            script = Script(key[0], key[1], scriptset=self)
            self.table[key] = script
            return script

    ##  Get the value for a key, if the script exists.

    def get (self, key):
        script = self.intern(key)
        if script.exists():
            return script

    ##  Like get(), but signals an error if the script does not exist.

    def __getitem__ (self, key):
        script = self.intern(key)
        if script.exists():
            return script
        else:
            raise KeyError('No such script: %s' % key)

    ##  Whether the key names an existing script.

    def __contains__ (self, key):
        return self.intern(key).exists()


##  A Scripts object for the data.seal directory.
scripts = Scripts(data.seal)


##  The base class for a script.

class BaseScript (object):

    ##  Constructor.

    def __init__ (self, suffix, scriptset=None):
        global scripts
        self._scriptset = scriptset or scripts
        self._suffix = suffix
        self._depth = None
        self._dependencies = None
        self._imports = None

    ##  The filename suffix.

    def suffix (self): return self._suffix

    ##  The scripts that this one imports.

    def imports (self): return self._imports or []

    ##  Returns the depth, defined as one greater than the maximal depth
    #   of any script that it imports.  Computed and cached the first time
    #   it is called.

    def depth (self):
        if self._depth is None:
            deps = self.dependencies()
            if deps:
                self._depth = max(s.depth() for s in deps) + 1
            else:
                self._depth = 0
        return self._depth

    ##  Returns the scripts this imports, the scripts they import, and so on.
    #   No script is repeated in the list.  Computed and cached the first time
    #   it is called.

    def dependencies (self):
        if self._dependencies is None:
            self._dependencies = self._compute_dependencies()
        return self._dependencies

    # my dependencies are scripts that have to be ordered before me

    def _compute_dependencies (self):
        found = set()
        todo = list(self.imports())
        while todo:
            s = todo.pop()
            if s is self:
                raise Exception('Circular dependency detected: %s' % s)
            if s not in found:
                found.add(s)
                todo.extend(s.dependencies())
        return sorted(found)


##  The main script class.

class Script (BaseScript):

    ##  Constructor.  We need the scriptset in order to take the transitive closure
    #   of the dependencies.

    def __init__ (self, name, suffix, scriptset=None):
        BaseScript.__init__(self, suffix, scriptset)
        self._name = name
        self._filename = os.path.join(self._scriptset.dir, name + '.' + suffix)

    ##  The name (excludes the suffix).

    def name (self): return self._name

    ##  The key, which is the pair (name, suffix).

    def key (self): return (self._name, self._suffix)

    ##  The filename.

    def filename (self): return self._filename

    ##  Whether it names an existing file.

    def exists (self): return os.path.exists(self._filename)

    ##  The hash value of the key.

    def __hash__ (self): return hash(self.key())

    ##  Two scripts are equal if they have the same key.

    def __eq__ (self, other): return self.key() == other.key()

    ##  Scripts are ordered by increasing depth, and alphabetically
    #   by key when the depths are the same.

    def __lt__ (self, other):
        d1 = self.depth()
        d2 = other.depth()
        if d1 < d2: value = True
        elif d1 > d2: value = False
        else: value = self.key() < other.key()
        #print('** LT', self, other, '->', value)
        return value

    ##  String representation.

    def __repr__ (self):
        return '<Script %s %s>' % (self._name, self._suffix)

    ##  The list of Scripts that this one imports.  It reads the beginning of
    #   the script file.  Import lines must be the first ones in the file,
    #   though they may be preceded by or interspersed with empty lines and
    #   comment lines (beginning with // or #).

    def imports (self):
        if self._imports is None:
            self._imports = [self._scriptset.intern(key) for key in self._read_imports()]
        return self._imports

    def _read_imports (self):
        if os.path.exists(self._filename):
            with open(self._filename) as f:
                try:
                    while True:
                        line = next(f).rstrip('\r\n')
                        if (not line or
                            line.isspace() or
                            line.startswith('#') or
                            line.startswith('//')):
                            continue
                        elif line.startswith('import '):
                            values = line[7:].rstrip(' ;').split(',')
                            for name in values:
                                yield (name.strip(), self._suffix)
                        else:
                            break
                except StopIteration:
                    pass

    ##  Returns the contents, omitting the import lines.

    def contents (self):
        if os.path.exists(self._filename):
            with open(self._filename) as f:
                try:
                    while True:
                        line = next(f)
                        if (line.isspace() or
                            line.startswith('#') or 
                            line.startswith('//') or
                            line.startswith('import ')):
                            continue
                        else:
                            break
                    while True:
                        yield line
                        line = next(f)
                except StopIteration:
                    pass


##  A set of scripts.

class ScriptList (BaseScript):

    ##  Constructor.

    def __init__ (self, suffix, scriptset=None):
        BaseScript.__init__(self, suffix, scriptset)
        self._imports = []

    ##  Whether the set is non-empty.

    def __bool__ (self): return bool(self._imports)

    ##  Whether the set contains a Script with the given name.

    def __contains__ (self, name):
        for s in self._imports:
            if s.name() == name:
                return True
        return False

    ##  Add the Script with the given name to the set.  No-op if
    #   it is already present.

    def append (self, name):
        s = self._scriptset.intern((name, self._suffix))
        if s not in self._imports:
            self._imports.append(s)
