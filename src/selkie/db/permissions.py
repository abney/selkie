##  @package seal.cld.db.permissions

import os
from seal.core.io import pprint, BackingSave
from seal.app.html import PermissionDenied, Row, String, TextBox
from seal.cld.db.meta import Metadata


##  The desktop user; automatically has permissions to do everything.
Root = '_root_'

##  Permissions granted to Everyone apply regardless of user name.
Everyone = 'everyone'


##  A metadata item representing permissions.  There are two specializations:
#   Permissions and GroupsFile.  Provides meta_permitted(), which requires
#   admin permission to all writing.

class PermItem (Metadata):

    ##  Constructor.  The host is a File.

    def __init__ (self, host):
        Metadata.__init__(self, host)
        self._loaded = False

    ##  Overrides Metadata.require_load.  It calls host._load_permissions(),
    #   which only loads the permissions metadata items and not the full file.

    def require_load (self):
        if not self._loaded:
            self.host._load_permissions()

    ##  Called by each update method.

    def writer (self):
        self.host.check_permission('admin')
        return Metadata.writer(self)

    ##  Whether one is allowed to perform the action on the Permissions item.
    #   Reading is always permitted.  Writing requires admin permission for the
    #   host.

    def meta_permitted (self, action, username=None):
        if action == 'read':
            return True
        elif action in ('write', 'admin'):
            return self.host.permitted('admin', username)
        else:
            raise Exception('Bad action: %s' % repr(action))


#--  Permissions  --------------------------------------------------------------

_role_index = {'owners': 0, 'editors': 1, 'shared': 2}

##  A set of permissions.

class Permissions (PermItem):

    ##  The item that the permissions belong to.
    #   We do not bake in any information from the parent,
    #   in case the parent's permissions get edited.

    def item (self):
        return self.host
    
    ##  Read the contents from a stream.
    #   Format of the file:
    #
    #      set TAB owners TAB owner1 owner2
    #      add TAB editors TAB editor1 editor2
    #      add TAB shared TAB reader1 reader2
    #
    #   Columns: mode, role, names
    #   Mode: 'set' - prevents inheritance.  'add' - enables inheritance.
    #   Roles: 'owner', 'editor', 'shared'.
    #   Namelist is a space-separated list of user/group names.

    def __read__ (self, f):
        # owners, editors, shared
        self._local = [set(), set(), set()]
        self._inherit = [True, True, True]
        for line in f:
            (mode, role, namelist) = line.rstrip('\r\n').split('\t')
            # set r
            r = _role_index[role]
            # mode
            if mode == 'add': self._inherit[r] = True
            elif mode == 'set': self._inherit[r] = False
            else: raise Exception('Bad mode: %s' % mode)
            # process names
            tgt = self._local[r]
            for name in namelist.split():
                name = name.strip()
                tgt.add(name)

    def _expand_user (self, username):
        if username is None:
            return set([Everyone])
        else:
            # guaranteed to contain Everyone
            return self.env.groups().all_groups(username)

    ##  Whether the user is permitted to do the action.
    #   Actions are 'read', 'write', and 'admin'.
    #   Owners may do all three, editors may read or write, and readers
    #   are only allowed to read.
    #
    #   It is tempting to try to cache this information when inherited,
    #   but one should resist the temptation.  Permissions of ancestors
    #   may get changed, causing undetected staleness in the cache.

    def permitted (self, action, username=None):

        # username
        if username is None: username = self.env['username']
        if username == Root: return True
        grps = self._expand_user(username) # set of user + ancestors

        # local
        if action == 'admin': mask = [True, False, False]
        elif action == 'write': mask = [True, True, False]
        elif action == 'read': mask = [True, True, True]
        else: raise Exception('Bad action: %s' % action)

        perm = self
        while any(mask):
            perm.require_load()
            for i in range(3):
                if mask[i]:
                    if grps & perm._local[i]:
                        return True
                    mask[i] = perm._inherit[i]
            parent = perm.item().parent()
            if parent is None: return False
            perm = parent.permissions()

    ##  The local (not inherited) permissions.  For display.

    def local (self):
        self.require_load()
        return self._local

    ##  The inherited permissions.  For display.

    def inherit (self):
        self.require_load()
        return self._inherit

    ##  Authorized users.  Returns a list of three sets: owners, editors, readers.

    def authorized_users (self):
        sets = [set(), set(), set()]
        mask = [True, True, True]
        item = self.item()
        perm = self
        while any(mask):
            perm.require_load()
            for i in range(3):
                if mask[i]:
                    sets[i].update(perm._local[i])
                    mask[i] = perm._inherit[i]
            item = item.parent()
            if item is None: break
            perm = item.permissions()
        return sets

    ##  Returns the authorized users for the parent.

    def inheritable (self):
        parent = self.item().parent()
        if parent is None: return [set(), set(), set()]
        else: return parent.permissions().authorized_users()

    ##  Checks whether the user is permitted to perform the action.
    #   Signals an error if not.

    def check (self, action, username=None):
        if not self.permitted(action, username):
            raise PermissionDenied('%s, item=%s, user=%s' % (action, repr(self.item()), username))


#     ##  This checks the permissions for the Permissions file itself.
#     #   Permissions files may be read by anyone, but only written by users
#     #   that have admin permission (i.e., owners).
# 
#     def check_permission (self, action):
#         if action == 'write':
#             self.check('admin') # i.e., admin permission for the protected file

    ##  Set the contents.

    def set (self, owners, editors, shared, inherit):
        assert isinstance(owners, list)
        assert isinstance(editors, list)
        assert isinstance(shared, list)
        assert isinstance(inherit, list)
        with self.writer():
            self.modified()
            sets = self._local
            sets[0] = set(owners)
            sets[1] = set(editors)
            sets[2] = set(shared)
            inh = self._inherit
            for i in range(3):
                inh[i] = False
            if inherit:
                for role in inherit:
                    i = _role_index[role]
                    inh[i] = True

    ##  Add the given user name to the local list of authorized users for
    #   the given role ('owner', 'editor', 'shared').

    def add (self, name, role):
        i = _role_index[role]
        with self.writer():
            self.modified()
            self._local[i].add(name)

    ##  Remove the given name from the local list of authorized users for the
    #   given role.

    def remove (self, name, role):
        i = _role_index[role]
        with self.writer():
            self.modified()
            self._local[i].remove(name)

    ##  Set the inheritability of the given role.  If a role is inheritable,
    #   permissions granted by the parent are inherited.  Otherwise, only
    #   local permissions are valid.

    def set_inheritable (self, role, value=True):
        i = _role_index[role]
        with self.writer():
            self.modified()
            self._inherit[i] = value

    ##  Write the contents to a stream.

    def __write__ (self, f):
        loc = self._local
        inh = self._inherit
        for (role, i) in _role_index.items():
            if inh[i]: mode = 'add'
            else: mode = 'set'
            f.write(mode)
            f.write('\t')
            f.write(role)
            f.write('\t')
            f.write(' '.join(loc[i]))
            f.write('\n')

    ##  Dump out the contents readably, for debugging.

    def dump (self):
        self.require_load()
        print('Permissions for', self.item())
        print('  Local:')
        loc = self._local
        inh = self._inherit
        for (role, i) in _role_index.items():
            if inh[i]: verb = 'add'
            else: verb = 'set'
            print('   ', verb, role + ':', ' '.join(loc[i]))
        print('  All authorized users:')
        sets = self.authorized_users()
        for (role, i) in _role_index.items():
            print('   ', role + ':', ' '.join(sorted(sets[i])))


#--  InheritedPermissions  -----------------------------------------------------

##  A permissions object that lacks local permissions.
#   All permissions are inherited.

class InheritedPermissions (Permissions):

    ##  Constructor.

    def __init__ (self, item):
        Permissions.__init__(self, item)
        self._local = [set(), set(), set()]
        self._inherit = [True, True, True]
        self._loaded = True

    ##  This is dispatched to the parent.
    #   Note that it affects not only this file but also the parent and siblings!
    #   Ditto for add, remove.

    def set (self, owners, editors, shared, inherit):
        perms = self.item().parent().permissions()
        perms.set(owners, editors, shared, inherit)

    ##  Dispatched to the parent.

    def add (self, name, role):
        perms = self.item().parent().permissions()
        perms.add(name, role)

    ##  Dispatched to the parent.

    def remove (self, name, role):
        perms = self.item().parent().permissions()
        perms.remove(name, role)

    ##  This is provided for the sake of form, but any attempt to set a value
    #   to False causes an error.

    def set_inheritable (self, role, value=True):
        if not value:
            raise Exception('File permissions are always inheritable')

    ##  Signals an error.

    def __write__ (self, f):
        raise Exception('File permissions cannot be separately written to disk')


#--  GroupsFile  ---------------------------------------------------------------

#
#  _parent_table maps user to list of parents
#  _ancestors_table maps user to set of ancestors, including self and Everyone
#
#  _parent_table lacks entries for users with no parents
#  _ancestors_table has entries for all mentioned users (excluding Everyone)
#

##  Information about which users belong to which groups.  Groups are actually
#   just users; any user may have members.

class GroupsFile (PermItem):

    ##  Read the contents from a stream.
    #   The format of a line: user parent1 parent2 ...

    def __read__ (self, f):
        self._parent_table = {}
        tab = self._parent_table
        for line in f:
            (k,v) = line.rstrip('\r\n').split('\t')
            tab[k] = v.split()
        self._compute_ancestors_table()

    ##  Write the contents to a stream.

    def __write__ (self, f):
        self.host.check_permission('admin')
        for (user, pars) in self._parent_table.items():
            print(user, ' '.join(pars), sep='\t', file=f)

    ##  The table of ancestors.  This is a dict that maps each user to
    #   the set of its ancestors.  A user is an ancestor of him/herself.

    def ancestors_table (self):
        if self._ancestors_table is None:
            self._compute_ancestors_table()
        return self._ancestors_table

    def _compute_ancestors_table (self):
        self._ancestors_table = {}
        lst = list(self._parent_table.keys())
        for user in lst:
            ancs = set([user, Everyone])
            self._ancestors_table[user] = ancs
            self._collect_user_ancestors(user, ancs)
    
    def _collect_user_ancestors (self, user, out):
        if user in self._parent_table:
            for parent in self._parent_table[user]:
                if parent not in out:
                    out.add(parent)
                    self._collect_user_ancestors(parent, out)
        else:
            self._ancestors_table[user] = set([user, Everyone])

    ##  Whether the user is in the ancestor table.
    #   Note that users without parent are present in the table; their
    #   ancestors include themselves and Everyone.

    def __contains__ (self, user):
        self.require_load()
        return self._ancestors_table.__contains__(user)

    ##  Iterate over the user names.

    def __iter__ (self):
        self.require_load()
        return self._ancestors_table.__iter__()

    ##  The number of user names.  (Does not count Everyone or Root.)

    def __len__ (self):
        self.require_load()
        return self._ancestors_table.__len__()

    ##  Iterates over the user names.

    def users (self): return self.__iter__()

    ##  The groups that this user immediately belongs to.

    def parents (self, user):
        self.require_load()
        if user in self._parent_table:
            return self._parent_table[user]
        else:
            return []

    ##  Returns the set of ancestors.  If user is not in the table at all,
    #   returns the set containing the user and Everyone.

    def all_groups (self, user):
        self.require_load()
        if user in self._ancestors_table:
            return self._ancestors_table[user]
        else:
            return set([user, Everyone])

    ##  Iterate over the members of a group.  This is inefficient, only
    #   for debugging or management.

    def members (self, group):
        self.require_load()
        for (user, grps) in self._parent_table.items():
            if group in grps:
                yield user

    ##  Iterate over the descendants of a group.  This is inefficient, only
    #   for debugging or management.

    def descendants (self, group):
        self.require_load()
        for (user, grps) in self._ancestors_table.items():
            if group in grps:
                yield user

    ##  Makes sure the user is present in the table, adding them if necessary.
    #   No return value.

    def intern (self, user):
        if user not in self:
            self.set_parents(user, tuple())

    ##  Sets the parents of the user.

    def set_parents (self, user, parents):
        with self.writer():
            parents = sorted(set(parents))
            tab = self._parent_table
            if user not in tab or tab[user] != parents:
                self.modified()
                tab[user] = parents
                # i'm lazy - just recompute the whole thing
                self._compute_ancestors_table()

    ##  Deletes the given user.

    def delete_user (self, user):
        with self.writer():
            tab = self._parent_table
            if user in tab:
                self.modified()
                del tab[user]
                self._compute_ancestors_table()

    ##  Print out all the contents readably, for debugging.

    def dump (self):
        self.require_load()
        print(repr(self))
        print('  Parents:')
        for (user, pars) in sorted(self._parent_table.items()):
            print('   ', user + ':', ' '.join(pars))
        print('  Ancestors:')
        for (user, ancs) in sorted(self._ancestors_table.items()):
            print('   ', user + ':', ' '.join(sorted(ancs)))
            
