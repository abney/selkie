##  @package seal.core.ssh
#   Execute an SSH request.

import pty, os, getpass, sys
from .io import pprint


#--  Server  -------------------------------------------------------------------

##  An SSH server.  Example:
#
#       >>> ssh = Server('oceanus.local', user='spa')
#       >>> s = ssh('ls')
#       >>> s = ssh.put('tmp.foo')
#       >>> s = ssh.get('tmp.2')
#

class Server (object):

    ##  Constructor.

    def __init__ (self, host, user=None):

        ##  The (remote) user.
        self.user = user or getpass.getuser()
        assert host and isinstance(host, str) and self.user and isinstance(self.user, str)

        ##  The remote host.
        self.host = host

        ##  The password.
        self.password = None

    ##  Has the form "user@host"

    def hoststring (self):
        return self.user + '@' + self.host

    ##  Has the form "user@host:path".

    def hostpath (self, path):
        return self.hoststring() + ':' + path

    ##  Returns a new Connection.

    def connection (self, show_progress=True, show_responses=True, return_responses=True):
        return Connection(self, show_progress, show_responses, return_responses)

#    def put (self, local, remote=None):
#        if remote is None: remote = local
#        rdir = os.path.dirname(remote)
#        if rdir:
#            self('mkdir -p ' + rdir)
#        return self.execute('scp', local, self.server.hostpath(remote))
#
#    def get (self, remote, local=None):
#        if local is None: local=remote
#        dir = os.path.dirname(local)
#        if dir:
#            if os.path.exists(dir):
#                if not os.path.isdir(dir):
#                    raise Exception('Not a directory: ' + dir)
#            else:
#                os.makedirs(dir)
#        return self.execute('scp', self.hostpath(remote), local)


#--  Connection  ---------------------------------------------------------------

##  An SSH connection.
#   The server contains persistent state: host, user, password.
#   The connection contains show_progress, show_responses, return_responses.
#   The connection can be thrown away, or used multiple times.

class Connection (object):

    ##  Constructor.

    def __init__ (self, server, show_progress=True, show_responses=True, return_responses=True):

        ##  The SSH Server.
        self.server = server

        ##  Whether to show progress.
        self.show_progress = show_progress

        ##  Whether to show responses from the server.
        self.show_responses = show_responses

        ##  Whether to return responses.
        self.return_responses = return_responses

        ##  Child PID.
        self.child_pid = None

        ##  Stream.
        self.stream = None

        ##  Pushback.
        self.pushback = None

    ##  The server hoststring.
    def hoststring (self): return self.server.hoststring()

    ##  The server hostpath.
    def hostpath (self, path): return self.server.hostpath(path)

    ##  If show_progress is enabled, prints the message.
    def progress (self, msg):
        if self.show_progress:
            pprint('[SSH: %s]' % msg, color='magenta')

    ##  Execute a remote command and return the value.
    def __call__ (self, cmd):
        return self.execute('ssh', self.server.hoststring(), cmd)

    #--  execute  --------------------------

    ##  Log in, send command, get response, return it.
    def execute (self, *argv):
        self._start(*argv)
        self._authenticate()
        s = self._get_response()
        self._shutdown()
        return s

    def _start (self, cmd, *args):
        (pid, f) = pty.fork()
        if pid == 0:
            os.execlp(cmd, cmd, *args)
        else:
            self.progress('Fork completed, child pid=%s' % pid)
            self.child_pid = pid
            self.stream = f

    def _read (self):
        x = None
        if self.pushback is not None:
            x = self.pushback
            self.pushback = None
        else:
            x = os.read(self.stream, 1024)
            if len(x) == 0: raise EOFError()
            self.progress('Read %s' % repr(x))
            if self.show_responses:
                pprint.now(x.decode('ascii'), color='cyan')
        return x

    def _write (self, b, dont_show=False):
        if not dont_show:
            pprint.now(b.decode('ascii'), color='green')
        os.write(self.stream, b)

    def _authenticate (self):
        self.progress('Authenticate')

        while True:
            self.progress('Reading')
            s = self._read()
    
            if b'authenticity of host' in s:
                self._authenticity_warning()
            
            elif b'Password:' in s or b'password:' in s:
                self.progress('Password request')
                if self.server.password is None:
                    self.progress('Getting password from user')
                    self.server.password = bytes(getpass.getpass(prompt='Password for %s: ' % self.server.hoststring()), 'ascii')
                self.progress('Sending password')
                self._write(self.server.password + b'\n', dont_show=True)
                self.progress('Checking response, first read')
                s = self._read()
                self.progress('Checking response, second read')
                s += self._read()
                if b'Permission denied' in s:
                    raise Exception('Invalid password')
                self.progress('Push back')
                self.pushback = s
                break

        self.progress('Authentication complete')

    def _authenticity_warning (self):
        self.progress('Authenticity warning, sending response')
        self._write(b'yes\n')
        while True:
            self.progress('Looking for confirmation')
            s = self._read()
            if b'ermanently added' in s:
                self.progress('Got confirmation')
                break

    def _get_response (self):
        try:
            if self.return_responses:
                output = bytearray()
    
            while True:
                self.progress('Reading response block')
                s = self._read()
                if self.return_responses:
                    self.progress('Append to output')
                    output += s

        except EOFError:
            self.progress('EOF')

        self.progress('Response complete')

        if self.return_responses:
            s = output.decode('ascii')
            if s.startswith('\r\n'): s = s[2:]
            return s

    def _shutdown (self):
        os.waitpid(self.child_pid, 0)
        os.close(self.stream)


#--  server  -------------------------------------------------------------------

##  A table mapping a host name to a server that connects to that host.

class ServerTable (object):

    ##  Constructor.
    def __init__ (self):

        ##  The contents, a dict.
        self.servers = {}

    ##  Fetch a server, creating it if necessary.

    def __call__ (self, host, user=None, show_progress=None, show_responses=None, return_responses=None):
        key = (host, user)
        if key in self.servers:
            svr = self.servers[key]
        else:
            svr = Server(host, user=user)
            self.servers[key] = svr
            if user is None:
                key = (svr.host, svr.user)
                if key in self.servers and self.servers[key] is not svr:
                    raise Exception('This cannot happen')
                self.servers[key] = svr
        return svr.connection(show_progress, show_responses, return_responses)

##  A ServerTable instance.
connection = ServerTable()
