##  @package seal.core.config
#   Configuration file.
#   This module contains only functionality that wraps the ~/.seal file.
#   For installation directories, see the seal.core.io Variables
#   and seal.core.version.

import os
from os.path import abspath, expanduser, exists, join
from .seal.version import Version, Revision, Patchlevel
from .seal import io
from .seal.io import Fn, pprint


##  The Seal directory.
sealdir = io.dest

##  The Seal directory.
dest = io.dest

##  For backwards compatibility.
Dest = dest

##  The Seal bin directory.
bin = io.bin

##  The seal examples directory.
ex = io.ex

##  The seal data directory.
data = io.data

##  The root directory.
root = io.root

##  The tmp directory.
tmp = io.tmp

##  The current directory, as an Fn.
here = io.here

##  The user's home directory, as an Fn.
home = io.home

##  Nowhere (/dev/null), as an Fn.
nowhere = io.nowhere

##  Returns a pathname relative to the Seal DEST directory.

def relpath (fn):
    if fn.startswith(dest + '/'):
        return fn[len(dest)+1:]
    else:
        raise Exception('Pathname is not relative to dest')

##  Configuration for Seal.

class Config (object):

    ##  Constructor.

    def __init__ (self, fn, strict=False):

        ##  Filename of the configuration file.
        self.filename = None

        ##  List of repositories.
        self.repos = {}

        ##  List of active directories.
        self.active = {}

        ##  Environment dict.
        self.environ = {}

        if fn:
            fn = os.path.expanduser(fn)
            self.filename = fn
            if os.path.exists(fn):
                with open(fn) as f:
                    for line in f:
                        fields = line.split()
                        if len(fields) >= 3:
                            type = fields[0]
                            if type in ('repo', 'active'):
                                key = fields[1]
                                value = fields[2:]
                                if type == 'repo':
                                    self.repos[key] = value
                                elif type == 'active':
                                    self.active[key] = value
                            elif type == 'set':
                                self.set(fields[1], fields[2])
                return

        if strict:
            raise Exception('Config file not found: %s' % fn)

    ##  Get the value of a configuration key.

    def get (self, keystr):
        tab = self.environ
        keys = keystr.split('.')
        for key in keys[:-1]:
            if key in tab:
                tab = tab[key]
                if not isinstance(tab, dict):
                    return None
            else:
                return None
        key = keys[-1]
        return tab.get(key)

    ##  Get a value and convert it to an absolute filename.

    def getfn (self, keystr):
        value = self.get(keystr)
        if value is None:
            return None
        elif value.startswith('/'):
            return Fn(value)
        elif value.startswith('~'):
            return Fn(expanduser(value))
        else:
            return Fn(abspath(value))

    ##  Set the value of a configuration key.

    def set (self, keystr, value):
        tab = self.environ
        tabs = [tab]
        keys = keystr.split('.')
        for key in keys[:-1]:
            if key in tab:
                tab = tab[key]
                if not isinstance(tab, dict):
                    print('**Bad setting:', keystr)
                    return
                tabs.append(tab)
            else:
                tab[key] = d = {}
                tab = d
                tabs.append(tab)
        key = keys[-1]
        tab[key] = self._replace_variables(value, tabs)

    def _replace_variables (self, value, tabs):
        frags = []
        k = 0
        while True:
            i = value.find('$', k)
            if i < 0 or i+1 >= len(value):
                if k == 0: return value
                if len(value) > k: frags.append(value[k:])
                break
            elif value[i+1] == '{':
                if i > 0: frags.append(value[:i])
                j = value.find('}', i+2)
                if j < 0:
                    vbl = value[i+2:]
                    j = len(value)
                else:
                    vbl = value[i+2:j]
                    j += 1
            else:
                j = self._end_of_word(value, i+1)
                vbl = value[i+1:j]
            if i > k: frags.append(value[k:i])
            repl = self._find_value(vbl, tabs)
            if repl: frags.append(repl)
            k = j
        if len(frags) == 1:
            return frags[0]
        else:
            return ''.join(frags)

    def _end_of_word (self, value, i):
        while i < len(value) and (value[i].isalnum() or value[i] == '_'):
            i += 1
        return i

    def _find_value (self, vbl, tabs):
        for i in range(len(tabs)-1, -1, -1):
            if vbl in tabs[i]:
                return tabs[i][vbl]
        return ''

    ##  Pretty-print.

    def __pprint__ (self):
        pprint('Config', self.filename)
        pprint('  Repositories:')
        for (name, value) in sorted(self.repos.items()):
            pprint('   ', name, ' '.join(value))
        pprint('  Active:')
        for (name, value) in sorted(self.active.items()):
            pprint('   ', name, ' '.join(value))


def _find_config_file ():
    if 'SEAL_CONFIG' in os.environ:
        return os.environ['SEAL_CONFIG']
    else:
        fn = expanduser('~/.seal')
        if exists(fn):
            return fn
        else:
            return abspath(join(sealdir, 'Config'))

##  The default configuration.
default = Config(_find_config_file())

##  Of the default configuration.
filename = default.filename

##  Of the default configuration.
repos = default.repos

##  Of the default configuration.
active = default.active

##  Of the default configuration.
environ = default.environ

##  For the default configuration.
__pprint__ = default.__pprint__

##  Method of the default configuration.
get = default.get

##  Method of the default configuration.
getfn = default.getfn


#--  Third-party data  ---------------------------------------------------------

##  CoNLL data directory.
conll = getfn('data.conll')

##  UDT data directory.
udt = getfn('data.udt')

##  Penn Treebank data directory.
ptb = getfn('data.ptb')

##  Perseus data directory.
perseus = getfn('data.perseus')

##  IDP data directory.
idp = dest/'thirdparty/idp'
