## @package seal.app.auth
#
#  Provides authentication.
#
#  Usage:
#
#      python auth.py set foo    # prompts for new password
#      python auth.py check foo  # prompts for password
#      python auth.py delete foo
#
#  It will prompt first for the password for salt.e.
#  Then it will prompt for the password you are setting or checking.
#
#  Python API:
#
#      auth = Authenticator(dir)
#      auth.check(user, password)  # returns True/False
#      auth.set(user, password)    # no return
#      auth.delete(user)
#
#  Perhaps I should have used the crypt module.
#

import os
from time import time
from hashlib import pbkdf2_hmac
from binascii import hexlify
from getpass import getpass
from subprocess import check_output
from seal.core.io import BackingSave
from seal.core.misc import run_main

#  Parameters

##  The size of the salt, in bytes.
SaltSize = 32

##  Which HMAC function to use in password hashing.
HMACFunction = 'sha512'

##  How many rounds of key generation to do.
KeyGenerationRounds = 100000

##  The size of the session key, in bytes.
SessionKeySize = 64

##  How often a session must be re-authenticated, in seconds.
SessionTimeout = 24 * 60 * 60   # 24 hours

##  How long a session can remain idle before timeout, in seconds.
IdleTimeout = 10 * 60           # 10 minutes


#--  Authenticator  ------------------------------------------------------------

##
#   An authenticator.
#

class Authenticator (object):


    ##  The constructor.
    #   @param request A Request.

    def __init__ (self, request):

        ##  The request.
        self.request = request

        ##  A LocalAuthenticator.
        #   Login, logout, and change_password are disabled if local is None.
        self.local = None

        ##  Logging function.
        self.log = request.log

        ##  User name.
        self.username = ''

        ##  Client address.
        self.client_addr = None

        ##  Cookie containing user name and session token, initially empty.
        #   Cookie does not get created until authentication is done.
        #   Setting a value in the cookie causes it to become modified
        #   and returned to the browser.  Hence we want to avoid using
        #   __setvalue__ for initialization.
        self.cookie = None


    ##  Authenticate the request.

    def authenticate (self):
        request = self.request

        self.local = None
        self.username = ''
        self.client_addr = request.client_addr()

        if request.doing_loopback_testing():
            self.log('auth', 'LOOPBACK TESTING')

        if request.execmode() == 'desktop':
            self.username = request.desktop_user()
            self.log('auth', 'Desktop mode, username=', repr(self.username))
            return True
    
        elif not request.connection_is_secure():
            self.log('auth', 'Connection not secure')
            return False

        elif request.server_authentication_on():
            self.username = request.server_username()
            if self.username:
                self.log('auth', 'Server authentication on, username=', repr(self.username))
            else:
                self.log('auth', 'Server authentication on, but no user')
            return bool(self.username)

        else:
            auth_dir = request.auth_dir()
            if not auth_dir:
                self.log('auth', 'No auth dir')
                return False

            else:
                self.local = LocalAuthenticator(auth_dir, self.log)
                status = self.local.authenticate(request)
                self._log_auth(status)
                self.username = status.user
                self.cookie = Cookie(user=status.user, token=status.token)
                return status.authenticated

    def _log_auth (self, status):
        if isinstance(status.token, str) and len(status.token) > 0:
            ts = 'token: %s...%s' % (status.token[:4], status.token[-4:])
        else:
            ts = 'token: %s' % repr(status.token)
        self.log('auth', status.authenticated, repr(status.user), status.reason, ts)


    ##  Log in, given user and password.

    def login (self, user, password):
        if self.local is not None:
            status = self.local.login(user, password, self.client_addr)
            self._log_auth(status)
            self.username = status.user
            self.cookie['user'] = status.user
            self.cookie['token'] = status.token
            return status.authenticated


    ##  Log out.

    def logout (self):
        if self.local is not None:
            user = self.cookie['user']
            token = self.cookie['token']
            status = self.local.logout(user, token)
            self.username = ''
            self.cookie['user'] = ''
            self.cookie['token'] = ''
            self.log('auth', status.authenticated, repr(status.user), status.reason)


    ##  Change password.

    def change_password (self, old_password, new_password):
        if self.username and self.local is not None:
            status = self.local.change_password(self.username, old_password, new_password)
            self.log('auth', 'Change password:', status.authenticated, status.reason)
            return status.authenticated

    ##  Headers for HTTP response.  Called by Response.http_headers().

    def response_headers (self):
        cookie = self.cookie
        if cookie is not None and cookie.modified:
            if self.request.doing_loopback_testing():
                secure = ''
            else:
                secure = 'Secure;'

            # this can cause trouble - there is no indication of path when cookies
            # come from the browser.
            # path = self.request.rootprefix() or '/'

            path = '/'

            for (k,v) in cookie.items():
                s = '%s=%s;path=%s;%sHttpOnly' % (k,v,path,secure)
                # self.log('auth', 'Set-Cookie', s)
                yield ('Set-Cookie', s)


#--  LocalAuthenticator  -------------------------------------------------------

##
#   Status is used to return information from the local authenticator.
#   If authenticated is False, then user and token are both ''
#

class Status (object):

    ##  Constructor.  Takes auth and reason, optionally user and token.

    def __init__ (self, auth, reason, user='', token=''):
        if auth: assert user
        else: assert not (user or token)
        
        ##  Whether the user is authenticated or not.
        self.authenticated = auth

        ##  The user name.  A string.
        self.user = user

        ##  The reason for the decision.
        self.reason = reason

        ##  The session token.
        self.token = token

    ##  True just in case the user has been authenticated.

    def __bool__ (self):
        return self.authenticated

    ##  Representation.

    def __repr__ (self):
        return '<Status %s %s u=%s t=%s>' % (self.authenticated, repr(self.reason), repr(self.user), repr(self.token))


##
#   A LocalAuthenticator does not do cookie updates; it functions statelessly
#   and locally.  Authenticator uses it as an interface to the authentication
#   directory.
#

class LocalAuthenticator (object):

    ##  Constructor.  Takes an authentication directory pathname.

    def __init__ (self, auth_dir, log=None):
        if not (isinstance(auth_dir, str) and auth_dir.startswith('/')):
            raise Exception('auth_dir must be absolute pathname')

        ##  The authentication directory.
        self.auth_dir = auth_dir

        ##  The log.
        self.log = log

        self._passwords = None
        self._sessions = None

    ##  Reads the users.txt file and returns a PasswordTable.
    #   Caches the result and re-uses it if called again.

    def passwords (self):
        if self._passwords is None:
            fn = os.path.join(self.auth_dir, 'users.txt')
            self._passwords = PasswordTable(fn)
        return self._passwords

    ##  Reads the sessions.txt file and returns a SessionsTable.
    #   Caches the result and re-uses it if called again.

    def sessions (self):
        if self._sessions is None:
            fn = os.path.join(self.auth_dir, 'sessions.txt')
            self._sessions = SessionsTable(fn)
        return self._sessions

    ##  Given a Request object, get the cookie and check it against
    #   the sessions table.

    def authenticate (self, request):
        # We cannot guarantee that the call comes from Authenticator
        if not request.connection_is_secure():
            return Status(False, 'NOT_SECURE')
        cookie = request.server_cookie()
        if not cookie:
            return Status(False, 'NO_COOKIE')
        # self.log('auth', 'Recd-Cookie', ';'.join('%s=%s' % (k,v) for (k,v) in cookie.items()))
        tab = self.sessions()
        return tab.check(cookie, request.client_addr())

    ##  Given a user name, password, and client address,
    #   authenticate the user and, on success, create a session entry.

    def login (self, user, password, address):
        passwords = self.passwords()
        status = passwords.check(user, password)
        if status.authenticated:
            sessions = self.sessions()
            status = sessions.set(user, address)
            return Status(True,
                          'Login: %s' % status.reason,
                          user=status.user,
                          token=status.token)
        else:
            return Status(False, 'FAILED_LOGIN: %s (user=%s, addr=%s)' % (status.reason, repr(user), repr(address)))

    ##  Delete the user from the sessions table, provided that the
    #   token matches the current session token.

    def logout (self, user, token):
        return self.sessions().unset(user, token)

    ##  Set the user's password in the password table.  Calls getpass()
    #   to get the password.

    def set_password (self, user, passwd=None):
        if passwd is None:
            passwd = getpass()
        self.passwords().set(user, passwd)
        self.sessions().delete(user)

    ##  Delete the user from both the password and sessions tables.

    def delete (self, user):
        self.passwords().delete(user)
        self.sessions().delete(user)

    ##  Change the user's password, provided that the given old_password is correct.

    def change_password (self, user, old_password, new_password):
        tab = self.passwords()
        status = tab.check(user, old_password)
        if status.authenticated:
            tab.set(user, new_password)
        return status

    ##  Print out user information from the password table.

    def print_user (self, user): self.passwords().print_user(user)

    ##  List the users that occur in the password table.

    def list_users (self): self.passwords().list_users()

    ##  Calls the password table's print_check() method.

    def print_check (self, user): self.passwords().print_check(user)
    

#--  PasswordTable  ------------------------------------------------------------

##
#   The in-memory representation of the users.txt file.
#

class PasswordTable (object):

    ##  An entry in the table.

    class Entry (object):
    
        ##  Constructor.  Requires user name.  Also accepts salt and hashed value.

        def __init__ (self, user, salt=None, hashed=None):
            if salt is None:
                if hashed is not None:
                    raise Exception('Must provide both salt and hashed or neither')
                salt = os.urandom(SaltSize).hex()
    
            ##  User name, a string.
            self.user = user

            ##  The salt.
            self.salt = salt

            ##  The hash value of the password.
            self.hashed = hashed
    
        ##  Return the hash value for a given password string.

        def hash (self, p):
            p = p.encode('ascii')
            salt = bytes.fromhex(self.salt)
            return pbkdf2_hmac(HMACFunction, p, salt, KeyGenerationRounds).hex()
    

    ##  Constructor.  Takes a filename.

    def __init__ (self, fn):

        ##  The filename of the users.txt file.
        self.filename = fn

        ##  A dict mapping user name to an Entry instance.
        self.entries = {}

        self._load()

    def _load (self):
        if os.path.exists(self.filename):
            with open(self.filename) as f:
                for line in f:
                    (user, salt, hashed) = line.rstrip('\n').split('\t')
                    self.entries[user] = self.Entry(user, salt, hashed)

    ##  Re-write the file from the current internal state.

    def save (self):
        with BackingSave(self.filename) as f:
            for ent in self.entries.values():
                f.write(ent.user)
                f.write('\t')
                f.write(ent.salt)
                f.write('\t')
                f.write(ent.hashed)
                f.write('\n')

    ##  Check whether a password is correct.  Returns a Status instance.

    def check (self, user, password):
        if user in self.entries:
            ent = self.entries[user]
            if ent.hashed == ent.hash(password):
                return Status(True, 'password authenticated', user=user)
            else:
                return Status(False, 'BAD PASSWORD (user=%s)' % repr(user))
        else:
            return Status(False, 'NO SUCH USER (user=%s)' % repr(user))

    ##  Set the user's password.

    def set (self, user, password):
        if user in self.entries:
            ent = self.entries[user]
        else:
            if any(c.isspace() for c in user):
                raise Exception('Space in user name: %s' % repr(user))
            ent = self.entries[user] = self.Entry(user)
        ent.hashed = ent.hash(password)
        self.save()

    ##  Delete the given user.

    def delete (self, user):
        if user in self.entries:
            del self.entries[user]
            self.save()

    ##  Print out whether the user exists in the table or not.

    def print_user (self, user):
        if user in self.entries:
            print('User exists:', repr(user))
        else:
            print('No such user:', repr(user))

    ##  Print out a list of user names.

    def list_users (self):
        for user in sorted(self.entries):
            print(user)

    ##  Get a password using getpass() and run a password check.

    def print_check (self, user):
        print(self.check(user, getpass()))


#--  Sessions  -----------------------------------------------------------------

##
#  For our purposes, it is fine to create a random session key and store it in a
#  file.  There will not be many active sessions.  The cookie only needs to
#  contain the user name and session key for authentication.  We can store the
#  expiration time, user address, and user port in the session-key file.
#
#  If we want to be even more secure, could use nonce tokens for every request -
#  the token can only be used once, and an attempt at re-use is recorded for
#  auditing and forces a fresh log-in.
#
#  Could also store a nonce token in each form.
#

class SessionsTable (object):

    ##  An entry in the table.

    class Entry (object):

        ##  Constructor.  Takes a user name.

        def __init__ (self, user):

            ##  User name.  A string.
            self.user = user

            ##  Session key, a.k.a. the token.
            self.sessionkey = None

            ##  Expiration time.
            self.expiration = None

            ##  How much time to add when renewing.
            self.renew_by = None

            ##  The client address.  Each session is valid for one user,
            #   and the user's client address may not change, unless the
            #   user re-authenticates.
            self.address = None
            
        ##  String representation.

        def __repr__ (self):
            return '<Entry %s %s %s %s %s>' % (repr(self.user),
                                               repr(self.sessionkey),
                                               repr(self.expiration),
                                               repr(self.renew_by),
                                               repr(self.address))


    ##  Constructor.  Takes the filename of the sessions.txt file.

    def __init__ (self, filename):

        ##  The filename of the sessions.txt file.
        self.filename = filename

        ##  The entries.  A dict mapping a user name to an Entry instance.
        self.entries = {}

        self._load()

    def _load (self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename) as f:
                    for line in f:
                        (user, key, exp, rb, addr) = line.rstrip('\n').split('\t')
                        ent = self.entries[user] = self.Entry(user)
                        ent.sessionkey = key
                        ent.expiration = float(exp)
                        ent.renew_by = float(rb)
                        ent.address = addr
            except:
                # Corrupted sessions file!
                if os.path.exists(self.filename):
                    os.unlink(self.filename)
                self.entries = {}

    ##  Write internal state back out to the file.

    def save (self):
        now = time()
        with BackingSave(self.filename) as f:
            for ent in self.entries.values():
                if ent.expiration > now:
                    f.write(ent.user)
                    f.write('\t')
                    f.write(ent.sessionkey)
                    f.write('\t')
                    f.write(str(ent.expiration))
                    f.write('\t')
                    f.write(str(ent.renew_by))
                    f.write('\t')
                    f.write(ent.address)
                    f.write('\n')

    ##  Look up the user, returning None if not found.

    def get (self, user): return self.entries.get(user)

    ##  Return the user's entry, signalling an error if not found.

    def __getitem__ (self, user): return self.entries.__getitem__(user)

    ##  Given a cookie and client address, check whether the token matches
    #   an active session.

    def check (self, cookie, address):
        user = cookie.get('user')
        if user is None:
            return Status(False, 'No user')

        ent = self.get(user)
        if ent is None:
            return Status(False, 'No session entry (user=%s)' % repr(user))

        if ent.sessionkey is None:
            return Status(False, 'Session entry contains no key (user=%s)' % repr(user))

        if ent.sessionkey != cookie.get('token'):
            return Status(False, 'Cookie token does not equal session key (user=%s)' % repr(user))

        now = time()

        if ent.expiration <= now or ent.renew_by + IdleTimeout <= now:
            return Status(False, 'Session key is expired (user=%s)' % repr(user))

        if ent.renew_by <= now:
            ent.renew_by = now + IdleTimeout
            self.save()

        if ent.address != address:
            return Status(False, 'Bad address (user=%s, addr=%s, expect=%s)' % (repr(user), repr(address), repr(ent.address)))

        reason = 'Good cookie (user=%s, addr=%s)' % (repr(user), repr(address))
        return Status(True, reason, user=user, token=ent.sessionkey)

    ##  Create a new session for the user, overwriting any old session.

    def set (self, user, address):
        assert isinstance(address, str)

        if user in self.entries:
            ent = self.entries[user]
            new = 'old'
        else:
            ent = self.entries[user] = self.Entry(user)
            new = 'new'
        ent.sessionkey = os.urandom(SessionKeySize).hex()
        now = time()
        ent.expiration = now + SessionTimeout
        ent.renew_by = now + IdleTimeout
        ent.address = address
        self.save()
        # setting cookie also sets cookie.modified = True
        # cookie['user'] = user
        # cookie['token'] = ent.sessionkey

        reason = '%s session (user=%s, addr=%s)' % (new, repr(user), repr(address))
        return Status(True, reason, user=user, token=ent.sessionkey)

    ##  Log out.  Delete the user's session, provided that the token is
    #   correct.

    def unset (self, user, token):
        if not user:
            result = 'No user provided'
        elif user not in self.entries:
            result = 'User not in sessions table'
        else:
            ent = self.entries[user]
            # cannot log out user if you are not authenticated as user
            if token != ent.sessionkey:
                result = 'Not logged out, token != session key'
            else:
                del self.entries[user]
                self.save()
                result = 'Logged out'

        return Status(False, 'Logout: %s (user=%s)' % (result, repr(user)))

    ##  Delete with prejudice.

    def delete (self, user):
        if user in self.entries:
            del self.entries[user]
            self.save()


##  A Cookie.

class Cookie (object):

    ##  Constructor.

    def __init__ (self, **kwargs):

        ##  The contents of the cookie.  A dict.
        self.contents = dict(kwargs.items())

        ##  Whether the cookie has been modified since its creation.
        self.modified = False

    ##  Fetch the value for a key.
    def __getitem__ (self, key): return self.contents[key]

    ##  Fetch the value for a key, returning None on failure.
    def get (self, key): return self.contents.get(key)

    ##  Iterates over the key-value pairs.
    def items (self): return self.contents.items()

    ##  Set the value of a key.  Sets self.modified to True.

    def __setitem__ (self, key, value):
        self.contents[key] = value
        self.modified = True

    ##  String representation.

    def __repr__ (self):
        return '<Cookie mod:%s %s>' % (self.modified, ','.join('%s=%s' % (k,repr(v)) for (k,v) in sorted(self.contents.items())))

