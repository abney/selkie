##  @package seal.app.config
#   Provides the Config class, which represents the contents of a configuration file.
#   It accommodates the case in which a configuration file is embedded within an
#   application file.

import os
from os import getcwd
from os.path import normpath, expanduser, join, dirname, exists
from io import StringIO
from inspect import isclass
from seal.core.io import abspath, load_dict, save_dict
from seal.core.misc import string_to_object
from seal.app.log import logger_from_config


def print_config (config, indent=0, file=None):
    indstr = ' ' * indent
    for (k,v) in config.items():
        print('%s%s:' % (indstr, k), repr(v), file=file)

def config_str (config, indent=0):
    with StringIO() as out:
        print_config(config, indent=indent, file=out)
        return out.getvalue()

def _path_components (fn):
    if not fn.startswith('/'):
        raise Exception('Not an absolute pathname: %s' % repr(fn))
    return fn[1:].split('/')

def _standardize_value (value, key):
    if value is not None:
        if key.endswith('_file') or key.endswith('_dir'):
            assert isinstance(value, str)
            if value:
                if value[0] == '~':
                    value = expanduser(value)
                elif value[0] not in '/@':
                    value = abspath(value)
        elif key == 'port' or key.endswith('_port') or key.endswith('_num'):
            value = int(value)
        elif key.endswith('_on'):
            value = bool(value)
#        elif key == 'app':
#            if isinstance(value, str):
#                value = string_to_object(value)
#                if isclass(value):
#                    value = value()
    return value

def standardize_config (config):
    for (k,v) in config.items():
        config[k] = _standardize_value(v, k)

# def _relativize_pathname (fn, writing_to):
#             
#             if value.startswith('/') or value == '-':
#                 pass
#             elif value.startswith('~'):
#                 value = expanduser(value)
#             else:
#                 if reading_from is not None:
#                     wd = dirname(reading_from)
#                 else:
#                     wd = getcwd()
#                 value = normpath(join(wd, value))
# 
#     home = expanduser('~/')
#     dir = dirname(writing_to)
#     if value is not None:
#         if key.endswith('_file') or key.endswith('_dir'):
#             if value.startswith('~'):
#                 return value
#             else:
#                 # dir is not necessarily cwd
#                 if not value.startswith('/'):
#                     value = os.path.abspath(value)
#                 dircpts = dir.split('/')
#                 valcpts = value.split('/')
#                 i = 0
#                 while i < len(valcpts) and i < len(dircpts) and valcpts[i] == dircpts[i]:
#                     i += 1
#                 if i >= len(dircpts):
#                     value = '/'.join(valcpts)
#                 else:
#                     j = len(dircpts) - i
#                     value = '../' * j + '/'.join(valcpts)
#     return value

def create_config (app=None, filename=None, items=None, defaults=None):
    cfg = {}
    if defaults:
        for (k,v) in defaults:
            cfg[k] = _standardize_value(v, k)
    if filename and os.path.exists(filename):
        for (k,v) in load_dict(filename).items():
            cfg[k] = _standardize_value(v, k)
    if items:
        for (k,v) in items:
            cfg[k] = _standardize_value(v, k)
    if app is not None:
        cfg['app'] = app
    if filename is not None:
        cfg['config_file'] = filename

    if cfg.get('log') is None:
        cfg['log'] = logger_from_config(cfg)

    return cfg


##
#   A Config object represents configuration information for an App.
#
class Config (object):

    ##  Constructor
    #
    #   First argument (settings) may be:</p>
    # 
    #    - a string ending in <tt>.cfg,</tt> which will be interpreted
    #      as the value of 'config_file'
    #    - any other string will be interpreted as the value of
    #      'application_file'
    #    - anything with an 'items' method (e.g., a dict or Config)
    #
    #  Any number of keyword arguments may be provided and interpreted as
    #  configuration settings.  They override previous settings.
    #
    #  As entries are added, the values are normalized.  The value of any
    #  key ending in '_file' or
    #  '_dir' is turned into an absolute path, and the value of 'port' or
    #  of any key ending in '_port' or '_num' is turned into an int.
    #
    #  If 'application_file' is provided but not 'config_file', then
    #  'config_file' is set to <i>dir</i><tt>/_config</tt> where <i>dir</i>
    #  is the value of 'application_file'.
    #

    def __init__ (self, fn=None, items=None, provenance=None, defaults=None):
        assert fn is None or items is None

        ##  Whether this is loaded from a file.
        self.filename = fn

        ##  The internal dict containing locally-set keys and values.
        self.contents = {}

        ##  A Config or dict from which additional keys are inherited.
        self.defaults = defaults

        self._provenance = {}

#        if settings is None:
#            pass
#        # this is a duplicate of code in parse_config
#        elif isinstance(settings, str):
#            if settings.endswith('.cfg'): key = 'config_file'
#            else: key = 'application_file'
#            self.set(key, settings, 'init')
#        elif isinstance(settings, (tuple, list)):
#            for (k,v) in settings:
#                self.set(k, v, 'init')
#        elif hasattr(settings, 'items'):
#            for (k,v) in settings.items():
#                self.set(k, v, 'init')
#        else:
#            raise Exception('Unrecognized initializer: %s' % repr(settings))

        if fn:
            if provenance is None: provenance = fn
            self.load(fn)
            self.set('config_file', fn, provenance)

        elif items:
            self.update(items, provenance)

    ##  The given items may be a list of pairs, or a dict or Config.
    #   Each key-value pair is passed to set().

    def update (self, items, provenance):
        if isinstance(items, (dict, Config)):
            items = items.items()
        for (k,v) in items:
            self.set(k, v, provenance)

    ##  Create a logger.

    def make_logger (self):
        return logger_from_config(self)

    ##  String representation.

    def __str__ (self):
        with StringIO() as f:
            print('Config:', file=f)
            for (k,v,p) in sorted(self.items_with_provenance()):
                print('    %s: %s [%s]' % (k, repr(v), p or '??'), file=f)
            return f.getvalue()

    ##  String representation.

    def __repr__ (self):
        s = ', '.join('%s: %s' % (repr(k), repr(v)) for (k,v) in self.contents.items())
        sep = ' ' if s else ''
        return '<Config%s%s>' % (sep, s)

    ##  Get the value for a key.

    def __getitem__ (self, key):
        if key in self.contents: return self.contents[key]
        elif self.defaults and key in self.defaults: return self.defaults[key]
        else: raise KeyError('No value for key: %s' % key)

    ##  Whether the key is present.

    def __contains__ (self, key):
        return (key in self.contents or
                (self.defaults and key in self.defaults))

    ##  Whether the config is non-empty.

    def __bool__ (self):
        return bool(self.contents)

    ##  Get the value for the key, or None.

    def get (self, key, default=None):
        if key in self.contents: return self.contents[key]
        elif self.defaults and key in self.defaults: return self.defaults[key]
        else: return default

    ##  Provenance of a setting.

    def provenance (self, key):
        if key in self.contents:
            return self._provenance[key]
        elif key in self.defaults:
            return 'default'

    ##  Iterate over the keys.

    def keys (self, include_defaults=True):
        for key in self.contents:
            yield key
        if include_defaults and self.defaults:
            for key in self.defaults.keys():
                if key not in self.contents:
                    yield key

    ##  Same as keys().

    def __iter__ (self):
        return self.keys()

    ##  Iterate over key-value pairs.

    def items (self, include_defaults=True):
        for item in self.contents.items():
            yield item
        if include_defaults and self.defaults:
            for (key,value) in self.defaults.items():
                if key not in self.contents:
                    yield (key,value)

    ##  Iterate over key-value pairs.

    def items_with_provenance (self, include_defaults=True):
        for (key, value) in self.contents.items():
            yield (key, value, self._provenance.get(key))
        if include_defaults and self.defaults:
            for (key, value) in self.defaults.items():
                if key not in self.contents:
                    yield (key, value, 'default')

    ##  Delete a key.

    def __delitem__ (self, key):
        if key in self.contents:
            del self.contents[key]
        else:
            raise Exception('Key is either not present or read-only: %s' % key)

    ##  Set the value for a key.

    def set (self, key, value, prov, relto=None):
        value = _standardize_value(value, key)
        self.contents.__setitem__(key, value)
        self._provenance[key] = prov
#         if value is not None:
#             if key == 'config_file':
#                 self._load(value)
#             elif key == 'application_file':
#                 self._load_appfile(value, prov)

    ##  Load does not set config_file - too easy to get clobbered by a setting
    #   among the keyword arguments to __init__.

    def load (self, cfn):
        if os.path.exists(cfn):
            for (k,v) in load_dict(cfn).items():
                if k == 'config_file':
                    raise Exception("Cannot specify 'config_file' inside config file")
                self.set(k, v, cfn, relto=cfn)

#     def _load_appfile (self, fn, prov):
#         if not self.contents.get('config_file'):
#             # setting 'config_file' triggers loading
#             self.set('config_file', join(fn, '_config'), prov)

    def _require_filename (self):
        cfn = self.get('config_file')
        if cfn:
            return self['config_file']
        else:
            raise Exception('Not set: config_file')

    ##  Setting values on the command line.

    def com_set (self, *settings):
        fn = self._require_filename()
        if exists(fn):
            d = load_dict(fn)
        else:
            d = {}
        for (k,v) in settings:
            if k == 'config_file':
                raise Exception('Cannot set config_file with com_set')
            self.set(k, v, 'com_set')
            d[k] = self.contents[k]
        save_dict(d, fn)

    ##  Deleting keys, from the command line.

    def com_unset (self, *keys):
        fn = self._require_filename()
        d = load_dict(fn)
        for key in keys:
            if key in ('config_file', 'application_file'):
                raise Exception('Not modifiable: %s' % key)
            if key in d:
                del d[key]
            if key in self.contents:
                del self.contents[key]
                del self._provenance[key]
        save_dict(d, fn)


#     
#     def _process_config (self, cfg):
#             self._process_dict(cfg.contents)
# 
#     def _process_command_line (self, words):
#         for word in words:
#             i = word.find('=')
#             if i < 0:
#                 self._process_config_file(word)
#             else:
#                 key = word[:i]
#                 value = word[i+1:]
#                 self.contents[key] = value
#     
#     def _process_dict (self, spec, table=None):
#         if table is None:
#             table = self.contents
#         todo = []
#         for (k,v) in spec.items():
#             i = k.find('.')
#             if i >= 0:
#                 if i == 0: raise Exception('Empty key: %s' % k)
#                 if i == len(k)-1: raise Exception('Empty tail: %s' % k)
#                 tail = k[i+1:]
#                 k = k[:i]
#                 if k in table:
#                     subtab = table[k]
#                     if not isinstance(subtab, dict):
#                         raise Exception('Inconsistent use of key: %s' % key)
#                     table[k][tail] = v
#                 else:
#                     table[k] = {tail:v}
#                     todo.append(k)
#             else:
#                 table[k] = v
#         for k in todo:
#             spec = table[k]
#             table[k] = {}
#             self._process_dict(spec, table[k])
# 


##
#   A config file.
#
class ConfigFile (object):

    ##  Constructor
    #
    #   First argument (settings) may be:</p>
    # 
    #    - a string ending in <tt>.cfg,</tt> which will be interpreted
    #      as the value of 'config_file'
    #    - any other string will be interpreted as the value of
    #      'application_file'
    #    - anything with an 'items' method (e.g., a dict or Config)
    #
    #  Any number of keyword arguments may be provided and interpreted as
    #  configuration settings.  They override previous settings.
    #
    #  As entries are added, the values are normalized.  The value of any
    #  key ending in '_file' or
    #  '_dir' is turned into an absolute path, and the value of 'port' or
    #  of any key ending in '_port' or '_num' is turned into an int.
    #
    #  If 'application_file' is provided but not 'config_file', then
    #  'config_file' is set to <i>dir</i><tt>/_config</tt> where <i>dir</i>
    #  is the value of 'application_file'.
    #

    def __init__ (self, fn):
        if not fn:
            raise Exception('Empty filename')

        self.filename = fn

        ##  The internal dict containing locally-set keys and values.
        self.contents = {}

        self.load(fn)

    ##  The given items may be a list of pairs, or a dict or Config.
    #   Each key-value pair is passed to set().

    def update (self, items):
        if isinstance(items, dict):
            items = items.items()
        for (k,v) in items:
            self.set(k, v)

    ##  String representation.

    def __str__ (self):
        with StringIO() as f:
            print('ConfigFile:', file=f)
            for (k,v) in sorted(self.contents.items()):
                print('    %s: %s' % (k, repr(v)), file=f)
            return f.getvalue()

    ##  String representation.

    def __repr__ (self):
        s = ', '.join('%s: %s' % (repr(k), repr(v)) for (k,v) in self.contents.items())
        sep = ' ' if s else ''
        return '<ConfigFile%s%s>' % (sep, s)

    ##  Get the value for a key.

    def __getitem__ (self, key):
        return self.contents.__getitem__(key)

    ##  Whether the key is present.

    def __contains__ (self, key):
        return self.contents.__contains__(key)

    ##  Whether the config is non-empty.

    def __bool__ (self):
        return self.contents.__bool__()

    ##  Get the value for the key, or None.

    def get (self, key, default=None):
        return self.contents.get(default)

    ##  Iterate over the keys.

    def keys (self):
        return self.contents.keys()

    ##  Same as keys().

    def __iter__ (self):
        return self.contents.__iter__()

    ##  Iterate over key-value pairs.

    def items (self):
        return self.contents.items()

    ##  Delete a key.

    def __delitem__ (self, key):
        self.contents.__delitem__(key)

    ##  Set the value for a key.

    def set (self, key, value):
        self.contents[key] = value

    ##  Load does not set config_file - too easy to get clobbered by a setting
    #   among the keyword arguments to __init__.

    def load (self, cfn):
        if os.path.exists(cfn):
            for (k,v) in load_dict(cfn).items():
                if k == 'config_file':
                    raise Exception("Cannot specify 'config_file' inside config file")
                self.set(k, v)

    ##  Setting values on the command line.

    def com_set (self, *settings):
        for (k,v) in settings:
            if k == 'config_file':
                raise Exception('Cannot set config_file with com_set')
            self.set(k, v)
        save_dict(self.contents, self.filename)

    ##  Deleting keys, from the command line.

    def com_unset (self, *keys):
        for key in keys:
            if key in ('config_file', 'application_file'):
                raise Exception('Not modifiable: %s' % key)
            elif key in self.contents:
                del self.contents[key]
        save_dict(self.contents, self.filename)
