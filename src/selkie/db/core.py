##  \package seal.cld.db.core
#   This package exists mainly to deal with dependency issues introduced by the types table.

from .disk import Disk
from .env import Environment
from .file import Integer, String, Strings, Table, PropDict
from .dir import Directory


##  Open an existing database.

def open_database (cls, filename, username='_root_', **kwargs):
    db = cls()
    db.env['filename'] = filename
    db.env['username'] = username
    db.env.update(kwargs)
    return db

##  Create and return a root File.

def create_database (cls, filename, force=False, username='_root_', **kwargs):
    db = open_database(cls, filename, username=username, **kwargs)
    db.create(force=force)
    return db

##  Delete a database.

def delete_database (filename):
    Disk().nuke(filename)
