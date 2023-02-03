##  @package seal.cld.ui.users
#   Provides UserListEditor and GroupsEditor.

from seal.app.html import *
from seal.cld.db.disk import writer
from seal.cld.ui.file import hex_encode, hex_decode


##  Groups editor.

class GroupsEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'home',
                 'user': 'user',
                 'adduser': 'adduser',
                 'post_user': 'post_user'}

    ##  Constructor.

    def __init__ (self, parent, groups):
        HtmlDirectory.__init__(self, parent)

        ##  A GroupsFile.
        self.groups = groups

    ##  The main entry point.

    def home (self):
        groups = self.groups
        users = groups.users()
        page = HtmlPage(self, title='Users')
        PathWithLogin(page)
        menu = MenuBar(page)
        Button(menu, '<<', '../')
        H1(page, 'Corpus Users')
        table = Table(page)
        row = Header(table)
        String(row, 'User')
        String(row, 'Groups')
        String(row, 'Edit')
        for user in sorted(users):
            row = Row(table)
            String(Cell(row), user)
            String(Cell(row), ' '.join(sorted(groups.parents(user))))
            Link(Cell(row), 'edit', 'user.%s' % hex_encode(user))
        Button(P(page), '+', 'adduser')
        return page

    ##  Callback to add a user.

    def adduser (self):
        return self._edituser1(action='new')

    ##  Callback to edit a user.

    def user (self, user):
        user = hex_decode(user)
        return self._edituser1(action='edit', id=user)

    def _edituser1 (self, id=None, action=None, groups=None, error=None):
        if action is None:
            if id is None: action = 'new'
            else: action = 'edit'
        if action == 'new': title = 'New User'
        else: title = 'Edit User'
        if groups is None:
            if action == 'new': groups = []
            else: groups = self.groups.all_groups(id) or []
        else:
            groups = groups.split()

        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        H1(page, title)
        if error:
            p = P(page)
            String(B(p), 'ERROR:')
            String(p, ' ')
            String(I(p), error)
        form = Form(page, 'post_user')
        Hidden(form, 'action', action)
        table = Table(form)
        row = Row(table)
        String(row, 'ID:')
        if action == 'new':
            TextBox(row, 'id', id or '')
        else:
            String(row, id)
            Hidden(form, 'id', id)
        row = Row(table)
        String(row, 'Groups:')
        TextBox(row, 'groups', ' '.join(groups))
        p = P(form)
        Submit(p, 'Submit')
        Submit(p, 'Delete User')
        Submit(p, 'Cancel')
        return page

    ##  Callback for the user-page form.

    def post_user (self, action=None, id=None, groups=None, submit=None):
        if submit == 'Cancel':
            return Redirect('.')
        elif not id:
            return self._edituser1(action=action, id=id, groups=groups,
                                   error='User ID is required')
        if groups: gids = groups.split()
        else: gids = []

        groups = self.groups
        with writer(groups):
            if submit == 'Delete User':
                groups.delete_user(id)
            else:
                groups.set_parents(id, gids)

        return Redirect('.')



#--  User List Editor  ---------------------------------------------------------

##  Edit a list of users.

class UserListEditor (HtmlDirectory):

    ##  Constructor.

    def __init__ (self, parent, users, groups):
        HtmlDirectory.__init__(self, parent)

        ##  The users.
        self.users = users

        ##  The groups.
        self.groups = groups

    ##  Maps page names to method names.
    __pages__ = {'': 'root',
                 'adduser': 'adduser',
                 'post_user': 'post_user',
                 'user': 'user'}

    ##  Main entry point.

    def root (self):
        users = self.groups.users
        page = HtmlPage(self, title='Users')
        PathWithLogin(page)
        menu = MenuBar(page)
        Button(menu, '<<', '../')
        H1(page, 'Corpus Users')
        p = P(page)
        first = True
        for user in sorted(users):
            if first: first = False
            else: BR(p)
            Link(p, user, 'user.%s' % user)
        Button(page, '+', 'adduser')
        return page

    ##  Produces a user page.

    def user (self, name):
        if name not in self.users:
            raise HttpUserException('Undefined user: %s' % name)
        return self._edituser1(name, action='edit')

    ##  Produces a user page editing a new user.

    def adduser (self):
        return self._edituser1()

    def _edituser1 (self, id=None, action=None, groups=None, error=None):
        if action is None:
            if id is None: action = 'new'
            else: action = 'edit'
        if action == 'new':
            title = 'New User'
        else:
            groups = self.groups.get(id)
            title = 'Edit User'

        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        H1(page, title)
        if error:
            p = P(page)
            String(B(p), 'ERROR:')
            String(p, ' ')
            String(I(p), error)
        form = Form(page, 'post_user')
        Hidden(form, 'action', action)
        table = Table(form)
        row = Row(table)
        String(row, 'ID:')
        if action == 'new':
            TextBox(row, 'id', id or '')
        else:
            String(row, id)
            Hidden(form, 'id', id)
        row = Row(table)
        String(row, 'Groups:')
        TextBox(row, 'groups', groups or '')
        p = P(form)
        Submit(p, 'Submit')
        Submit(p, 'Cancel')
        return page

    ##  Callback from the user page.

    def post_user (self, action=None, id=None, groups=None, submit=None):
        if submit == 'Cancel':
            return Redirect('.')
        elif not id:
            return self._edituser1(action=action, id=id, groups=groups,
                                   error='User ID is required')
        users = self.users
        bad = []
        if not safe_name(id): bad.append(id)
        if groups:
            gids = groups.split()
            for gid in gids:
                if not safe_name(gid): bad.append(gid)
        else:
            gids = []

        if bad:
            return self._edituser1(action=action, id=id, groups=groups,
                                   error='Illegal ID(s): ' + ' '.join(bad))

        if action == 'new': user = users.new_child(id)
        else: user = users[id]

        for g in gids: users.intern(g)
        groups = ' '.join(sorted(gids))

        old_groups = user.get('groups') or ''
        if groups != old_groups:
            with writer(user):
                user['groups'] = groups
        return Redirect('.')

