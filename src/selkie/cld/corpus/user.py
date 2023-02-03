##  @package seal.cld.corpus.user
#   Contains User and supporting classes.

import os
from seal.core.misc import isword
from seal.cld.db.file import File, PropDict
from seal.cld.db.dir import Directory, Structure
from seal.cld.db.permissions import Everyone
from seal.cld.corpus.media import MediaIndex


##  A user.
#   Note that user.name() is defined.

class User (Structure):

    ##  Maps child name to class.
    signature = {'props': PropDict,
                 'media': MediaIndex}


##  Used if there is no actual property dict.

class FakePropDict (object):

    ##  Always returns False.

    def __contains__ (self, key):
        return False

    ##  Signals an error.

    def __getitem__ (self, key):
        raise Exception('No value for key: %s' % key)

    ##  Signals an error.

    def __setitem__ (self, key, value):
        raise Exception('FakePropDict is read-only')


_fakepropdict = FakePropDict()


##  The unknown user.  Its property dict is the fake prop dict.

class UnknownUser (object):

    ##  Constructor.

    def __init__ (self, name):
        self._name = name

    ##  Name.

    def name (self): return self._name

    ##  Fetching 'props' or 'media' returns a fake prop dict.  Anything
    #   else signals an error.

    def __getattr__ (self, att):
        if att in ('props', 'media'):
            return _fakepropdict
        else:
            raise AttributeError("%s has no attribute '%s'" % (self, att))


##  List of users.

class UserList (Directory):
    
    ##  Child type is User.
    childtype = User

    ##  Fetch one, or None on failure.
    #   Returns the User with the given <i>name.</i>  If <i>name</i> is
    #   None or there is no such user, return value is UnknownUser,
    #   unless <i>allow_unknown</i> is False, in which case the return is None.

    def get (self, name, allow_unknown=True):
        if name is None and allow_unknown:
            return UnknownUser('')
        elif name in self:
            return self[name]
        elif allow_unknown:
            return UnknownUser(name)

    ##  Fetch one, creating a new one if necessary.

    def intern (self, name):
        if name in self:
            return self[name]
        else:
            self.env.groups().intern(name)
            return self.new_child(name)

    ##  Create a new user.
    #   Checks that the given name is a word (only alphanumerics and underscore,
    #   not empty).

    def new_child (self, name):
        if not isword(name):
            raise Exception('Illegal username: %s' % repr(name))
        return Directory.new_child(self, name)
