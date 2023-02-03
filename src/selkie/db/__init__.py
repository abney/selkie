##  @package seal.cld.db
#   File-backed database.

import .env
from .file import File, Integer, String, Strings, Table, PropDict
from .dir import Directory


##  Set the 'default_types' member of env here, because the classes we need were
#   not defined when Environment was declared.

env.default_types = {'int': Integer,
                     'str': String,
                     'strs': Strings,
                     'tab': Table,
                     'pd': PropDict,
                     'dir': Directory}
