##  @package seal.cld.toplevel
#   Toplevel calls, for the CLD script.

from sys import stdout
from os import getenv
from os.path import join, dirname, exists
from seal.core.config import environ
from seal.core.io import ex, abspath
from seal.core.sh import mkdir, cp, rmrf
from seal.app import toplevel
from seal.app.auth import LocalAuthenticator
from seal.app.toplevel import Command, Manager
from seal.app.parse import parse_config
from seal.app.config import Config, print_config
from seal.app.server import create_cert
from seal.cld.corpus.core import open_corpus, Corpus
from seal.cld.corpus.export import CorpusContainer
from seal.cld.corpus.export_file import ExportFile
from seal.cld.core import CLD


##  A test context.

class TestContext (object):

    ##  Constructor.

    def __init__ (self, config):

        ##  The user name.
        self.username = config.get('username')

        ##  Config.
        self.config = config

def _cld_config (cfg, kwargs=None):
    cfg = parse_config(cfg, kwargs)    
    if not cfg.get('app'):
        cfg.set('app', CLDApp(), '_cld_config')
    return cfg

def _load_corpus (cfg, kwargs=None):
    orig = cfg
    cfg = _cld_config(cfg, kwargs)
    fn = cfg['application_file']
    if not fn:
        raise Exception('No application file in configuration %s' % orig)
    return open_corpus(fn, context=TestContext(cfg))

def _corpus_container (cfg, kwargs=None):
    return CorpusContainer(_load_corpus(cfg, kwargs))


#--  File/Directory information  -----------------------------------------------

def _permissions_string (item):
    users = item.permissions().authorized_users()
    words = [(','.join(sorted(s)) or '-') for s in users]
    return ' '.join(words)

def _print_info (item):
    stdout.write('%s %s %s\n' % (item.name(),
                                 item.__class__.__name__,
                                 _permissions_string(item)))


#--  Users and groups  ---------------------------------------------------------

def _print_user_info (groups, username):
    print('User:      ', username)
    print('Member of: ', ' '.join(groups.parents(username)))
    print('Indirectly:', ' '.join(groups.all_groups(username)))

def _print_group_info (groups, group):
    print('Group:      ', group)
    print('Members:    ', ' '.join(sorted(groups.members(group))))
    print('Descendants:', ' '.join(sorted(groups.descendants(group))))

def _groups_add (groups, username, group):
    parents = groups.parents(username)
    if group not in parents:
        groups.set_parents(username, parents + [group])
        return True

def _groups_remove (groups, username, group):
    parents = groups.parents(username)
    if group in parents:
        parents = list(parents)
        parents.remove(group)
        groups.set_parents(username, parents)
        return True


#--  Commands  -----------------------------------------------------------------

##  Example corpus.  Example of use:
#
#       with ExampleCorpus() as corpus:
#           corpus('/langs/lang.oji/home').describe()
#

class ExampleCorpus (object):

    ##  Constructor.

    def __init__ (self, fn):
        fn = abspath(fn)
        if fn.endswith('.d'):
            self._server_dir = fn
            self._filename = join(fn, 'corpus.cld')
            self._media = join(fn, 'media')
            self._auth = join(fn, 'auth')
            self._cert_file = join(self._auth, 'cert.crt')
        elif fn.endswith('.cld'):
            self._filename = fn
            self._server_dir = None
            self._media = join(fn, '_media')
            self._auth = None
            self._cert_file = None
        else:
            raise Exception('Unrecognized filename suffix: %s' % repr(fn))

        self._logging = 'traceback'

        # set on __enter__
        self._manager = None
        self._rtfunction = None

    ##  Returns the corpus filename.

    def filename (self):
        return self._filename

    ##  Enter.  Calls self.create().

    def __enter__ (self):
        self.create()
        self._manager = CLDManager(self._filename,
                                   execmode='desktop',
                                   logging=self._logging,
                                   log_file='-')
        self._rtfunction = self._manager.open()
        self._rtfunction.__enter__()
        return self

    ##  Exit.  Calls self.delete().

    def __exit__ (self, t, v, tb):
        self._rtfunction.__exit__(t,v,tb)
        self._rtfunction = None
        self.delete()

    ##  Create the corpus and media directories.

    def create (self,
                item_file=ex/'corp2.ef',
                user_name=getenv('USER'),
                user_files=[ex/'tuebingen.mp3']):
        if self._server_dir and not exists(self._server_dir):
            mkdir(self._server_dir)
        self._create_corpus(item_file, user_name)
        self._create_media(user_name, user_files)
        self._create_auth(user_name)

    ##  Delete the corpus and media directories (recursively).

    def delete (self):
        print('Delete corpus', repr(self._filename))
        rmrf(self._filename)
        print('Delete media', repr(self._media))
        rmrf(self._media)

    def _create_corpus (self, item_file, user_name):
        corpus = self._filename
        print('Create corpus', repr(corpus))
        rmrf(corpus)
        mgr = CLDManager(corpus)
        mgr.create()
        if self._media:
            mgr.set(('media_dir', self._media))
        if self._auth:
            mgr.set(('auth_dir', self._auth))
        if self._cert_file:
            mgr.set(('cert_file', self._cert_file))
        mgr.import_from(item_file)
        mgr.perm_add('/', user_name, 'owners')

    def _create_media (self, user_name, user_files):
        media = self._media
        if media:
            print('Create media', repr(media))
            rmrf(media)
            mkdir(media)
            udir = join(media, user_name)
            mkdir(udir)
            for fn in user_files:
                cp(fn, udir)

    def _create_auth (self, user_name):
        authdir = self._auth
        if authdir:
            if not exists(authdir):
                print('Create auth', repr(authdir))
                mkdir(authdir)
            print('Create certificate', repr(self._cert_file))
            create_cert(self._cert_file)
            auth = LocalAuthenticator(self._auth)
            auth.set_password(user_name, 'foo')

    ##  Execute a request.

    def __call__ (self, req):
        if self._rtfunction is None:
            raise Exception('Must be called within with-statement')
        print('Request', repr(req))
        return self._rtfunction(req)


#--  CorpusCommand  ------------------------------------------------------------

##  Command that needs a corpus.

class AbstractCorpusCommand (Command):

    ##  Constructor.

    def __init__ (self, *args):
        Command.__init__(self, *args)
        self._corpus = None
        self._groups = None

    ##  The corpus filename.

    def filename (self):
        fn = self.config.get('application_file')
        if not fn:
            print(self.config)
            raise Exception('Not specified: application_file')
        return fn

    ##  Loads and returns the Corpus.

    def corpus (self):
        if self._corpus is None:
            self._corpus = open_corpus(self.filename(), context=TestContext(self.config))
        return self._corpus
    
    ##  Fetches the GroupsFile.

    def groups (self):
        if self._groups is None:
            self._groups = self.corpus().env.groups()
        return self._groups

    ##  Loads and returns the File with the given pathname.

    def item (self, pathname):
        return self.corpus().follow(pathname)


#--  CorpusCommand  ------------------------------------------------------------

##  Command for manipulating corpus file.

class CorpusCommand (AbstractCorpusCommand):

    ##  Create a new corpus.

    def create (self):
        corpus = self.corpus()
        corpus.create()
        config = corpus.config()
        if config.get('auth_dir') is None:
            config.com_set(('auth_dir', 'auth'))
        if config.get('media_dir') is None:
            config.com_set(('media_dir', 'media'))

    ##  Create a copy of the test corpus.

    def create_test (self, **kwargs):
        corpus = ExampleCorpus(self.subject)
        corpus.create(**kwargs)

    ##  Print out corpus information.

    def item_info (self, item=''):
        item = self.corpus().follow(item)
        _print_info(item)

    ##  List the disk directory of the named item.

    def ls (self, item=None):
        corpus = self.corpus()
        item = corpus.follow(item)
        if item.is_directory():
            names = list(item)
            if not names:
                print('(empty directory)')
            else:
                colwidth = max(len(nm)+1 for nm in names)
                ncols = 80 // colwidth
                nrows = len(names) // ncols
                if ncols * nrows < len(names): nrows += 1
                for i in range(nrows):
                    for j in range(ncols):
                        k = i * ncols + j
                        if k >= len(names):
                            break
                        stdout.write('%-*s' % (colwidth, names[k]))
                    stdout.write('\n')
        else:
            _print_info(item)
    
    ##  Delete the named item from the corpus.

    def rm (self, path):
        corpus = self.corpus()
        file = corpus.follow(path)
        file.delete()
    
    ##  Print out the corpus contents as a tree.

    def tree (self, **kwargs):
        self.corpus().print_tree()


#--  ExportCommand  ------------------------------------------------------------

##  An export-related command.

class ExportCommand (AbstractCorpusCommand):

    ##  Create a CorpusContainer.

    def container (self):
        return CorpusContainer(self.corpus())

    ##  List items in the corpus.

    def com_list (self, *sel):
        self.container().com_list(*sel)

    ##  Delete the given items.

    def com_delete (self, *sel):
        self.container().com_delete(*sel)

    ##  Export the given items to the given export file.

    def com_export (self, fn, *sel):
        self.container().com_export(fn, *sel)

    ##  Import the given items from the given export file.

    def com_import (self, fn, *sel):
        self.container().com_import(fn, *sel)


#--  ExportFileCommand  --------------------------------------------------------

##  An command for managing ef files.

class ExportFileCommand (Command):

    def __init__ (self, *args):
        Command.__init__(self, *args)
        self._exportfile = ExportFile(self.config['application_file'])

    def ls (self, *items):
        if items:
            for item in items:
                self._exportfile.print_item(item)
        else:
            self._exportfile.print_listing()

    def extract_all (self, dir=None):
        self._exportfile.extract_all(dir)

    def print_item (self, item):
        self._exportfile.print_item(item)


#--  GLabCommand  --------------------------------------------------------------

##  A GLab-related command.

class GLabCommand (CorpusCommand):

    ##  List the user's notebooks, or the list of users if no user is provided.

    def ls (self, *users):
        if users:
            for user in users:
                CorpusCommand.ls(self, 'glab/' + user)
        else:
            CorpusCommand.ls(self, 'glab')

    ##  Add the given users.

    def add (self, *users):
        if users:
            corpus = self.corpus()
            dir = corpus['glab']
            dir.add_users(users)

    ##  Delete the given users.

    def rm (self, *users):
        if users:
            corpus = self.corpus()
            dir = corpus['glab']
            dir.delete_users(users)


#--  GroupsCommand  ------------------------------------------------------------

##  A group-related command.

class GroupsCommand (AbstractCorpusCommand):
    
    ##  List the members of the group.

    def ls (self, group=None):
        groups = self.groups()
        if group is None:
            groups.dump()
        else:
            _print_group_info(groups, group)

    ##  Add the users to the group.

    def add (self, group, *users):
        groups = self.groups()
        for user in users:
            _groups_add(groups, user, group)
        _print_group_info(groups, group)

    ##  Remove the users from the group.

    def rm (self, group, *users):
        groups = self.groups()
        for user in users:
            _groups_remove(groups, user, group)
        _print_group_info(groups, group)


#--  PermissionsCommand  -------------------------------------------------------

##  A permissions-related command.

class PermissionsCommand (AbstractCorpusCommand):

    ##  Print out the permissions for the named item.
    #   Example: cld corpus.cld perm language/oji

    def ls (self, pathname):
        item = self.item(pathname)
        print(_permissions_string(item))

    ##  Enable the role for the user with respect to the named item.
    #   Example: cld corpus.cld perm language/oji add abney editor.

    def add (self, pathname, user, role):
        if role not in ('owners', 'editors', 'shared'):
            raise Exception('Legal roles are owners, editors, shared: %s' % repr(role))
        item = self.item(pathname)
        item.permissions().add(user, role)
        print(_permissions_string(item))

    ##  Disable the role for the user with respect to the named item.

    def rm (self, pathname, user, role):
        if role not in ('owners', 'editors', 'shared'):
            raise Exception('Legal roles are owners, editors, shared: %s' % repr(role))
        item = self.item(pathname)
        item.permissions().remove(user, role)
        print(_permissions_string(item))


#--  UsersCommand  -------------------------------------------------------------

##  A command for managing users.

class UsersCommand (AbstractCorpusCommand):
    
    ##  Print out information about the user, or about all users/groups
    #   if no user is provided.

    def ls (self, user=None):
        groups = self.groups()
        if user is None:
            groups.dump()
        else:
            _print_user_info(groups, user)

    ##  Add the user to the group.

    def add (self, user, group):
        groups = self.groups()
        if _groups_add(groups, user, group):
            _print_user_info(groups, user)
        else:
            print('Already a member, no action taken')

    ##  Remove the user from the group.

    def rm (self, user, group):
        groups = self.groups()
        if _groups_remove(groups, user, group):
            _print_user_info(groups, user)
        else:
            print('Not an (immediate) member of the group, no action taken')


#--  Manager  ------------------------------------------------------------------

_usage = '''Usage:
cld CFN [KW*]
cld CFN [KW*] call PATH [KVPAIR*]
cld CFN [KW*] config
cld CFN [KW*] create|-c
cld CFN [KW*] create_cgi CGIFN [KW*]
cld CFN [KW*] create_test
cld CFN [KW*] delete|del|-d [LANG] [ITEM*]
cld CFN [KW*] export|-e EFN [LANG] [ITEM*]
cld CFN [KW*] glab
cld CFN [KW*] group
cld           help|--help|-?
cld CFN [KW*] import|-i EFN
cld CFN [KW*] info
cld CFN [KW*] list|-l [ITEM*]
cld CFN [KW*] ls
cld CFN [KW*] perm
cld CFN [KW*] rm
cld CFN [KW*] run
cld CFN [KW*] set [KW*]
cld CFN [KW*] tree [KW*]
cld CFN [KW*] unset [KEY*]
cld CFN [KW*] user

The cld module manages the CLD application and associated 
application files.  The first argument ('CFN') is an
application file.  The second argument is the command.
If there is no command, it defaults to 'run'.  The argument
types are:

   CGIFN   the filename of a CGI file
   EFN     the filename of an export file
   LANG    a language code
   ITEM    an item ID
   KVPAIR  a key-value pair; allows duplicate keys
   KW      a key-value pair; does not allow duplicate keys
   KEY     a configuration key


--  COMMANDS  ----------------------------------------------

call
    Instantiate the app and run it.  That is, run
    Python web server that calls back to the app to
    handle requests.  Then, for each PATH, execute
    an HTTP request to the server.  This emulates
    what a web browser does.  Finally, the HTTP
    response is printed out.
    
config
    Print out the app configuration.

create
    Create the named corpus directory.

create_cgi
    Create a CGI file that uses the named corpus.

create_test
    Creates a test corpus.  Prepopulates it from seal/examples/corp1.ef.
    Also creates a media directory.  If not otherwise specified, the
    media directory will be called 'media' in the current directory.

delete
    Delete the indicated items.

export
    Export the indicated items to EFN.  If no items are named, the entire
    corpus is exported.

glab

group

help
    Print out this help message.

import
    Import from EFN.

info

list
    List the named items.  If none are specified, list the entire corpus.

ls

perm

rm

run
    Run the CLD application.  This is the default, if no command is provided.

set
    Set values of configuration keys.

tree
    Print out the contents of the corpus in tree format.

unset
    Unset values of configuration keys.

user
'''



##  Specialization of Manager for use with CLD.

class CLDManager (Manager):

    ##  Same as Manager.defaults, except that it adds 'media_dir'.

    __defaults__ = dict(Manager.__defaults__, 
                        app = CLD,
                        media_dir = None)

    __commands__ = dict(Manager.__commands__,
                        corpus = (CorpusCommand, 'corpus', ''),
                        create = (CorpusCommand, 'create', ''),
                        create_test = (CorpusCommand, 'create_test', '@'),
                        delete = (ExportCommand, 'com_delete', '*'),
                        ef_list = (ExportFileCommand, 'ls', '*'),
                        export_to = (ExportCommand, 'com_export', '!*'),
                        extract = (ExportFileCommand, 'extract_all', '?'),
                        get = (ExportFileCommand, 'print_item', '!'),
                        glab_ls = (GLabCommand, 'ls', '*'),
                        glab_add = (GLabCommand, 'add', '*'),
                        glab_rm = (GLabCommand, 'rm', '*'),
                        group = (GroupsCommand, 'ls', '?'),
                        group_add = (GroupsCommand, 'add', '!*'),
                        group_rm = (GroupsCommand, 'rm', '!*'),
                        # any list of items is currently ignored
                        import_from = (ExportCommand, 'com_import', '!*'),
                        info = (CorpusCommand, 'item_info', '?'),
                        items = (ExportCommand, 'com_list', '*'),
                        ls = (CorpusCommand, 'ls', '?'),
                        perm = (PermissionsCommand, 'ls', '!'),
                        perm_add = (PermissionsCommand, 'add', '!!!'),
                        perm_rm = (PermissionsCommand, 'rm', '!!!'),
                        rm = (CorpusCommand, 'rm', '!'),
                        tree = (CorpusCommand, 'tree', '@'),
                        user = (UsersCommand, 'ls', '?'),
                        user_add = (UsersCommand, 'add', '!!'),
                        user_rm = (UsersCommand, 'rm', '!!'))

    ##  Adds the '.d' case.  (Called by Manager.__init__.)
    
    def __configfile__ (self, subject):
        if subject.endswith('.cfg'):
            return subject
        elif subject.endswith('.cld'):
            return join(subject, '_config')
        elif subject.endswith('.d'):
            return join(subject, 'corpus.cld', '_config')

    ##  Constructor.

    #   _subject is explicitly mentioned so that CLDManager(fn) works.

    def __init__ (self, _subject=None, **kwargs):
        Manager.__init__(self, _subject, **kwargs)
        subject = self.__subject__  # absolute pathname
        if subject and subject.endswith('.d'):
            cfg = self.__config__
            cfg['server_dir'] = subject
            cfg['application_file'] = join(subject, 'corpus.cld')
            if not cfg.get('media_dir'):
                cfg['media_dir'] = join(subject, 'media')
            if not cfg.get('auth_dir'):
                cfg['auth_dir'] = join(subject, 'auth')
            if not cfg.get('cert_file'):
                cfg['cert_file'] = join(subject, 'auth', 'cert.crt')
