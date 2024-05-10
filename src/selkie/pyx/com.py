'''
The selkie.com module contains functionality related to command-line processing,
as well as system commands.
'''

import sys, subprocess
from time import time
from .string import elapsed_time_str


#--  file_size  ----------------------------------------------------------------

def file_size (fn):
    '''
    Returns the file size in bytes.
    '''
    return os.stat(fn).st_size


#--  wget  ---------------------------------------------------------------------

##  Simple interface to urlretrieve().

def wget (url):
    return urllib.request.urlretrieve(url)[0]


#--  System calls  -------------------------------------------------------------

def system (*args, silent=False):
    '''
    Runs a command line represented as separate words.
    Returns True on success, False on failure.
    Keyword argument silent=True suppresses any printout.
    '''
    return True if subprocess.run(args, capture_output=silent).returncode == 0 else False

def backtick (*args):
    '''
    Runs a command line represented as separated words.
    Returns the printed output, as a string.
    Signals an error if the call does not succeed.
    '''
    return subprocess.run(args, check=True, capture_output=True, text=True)


#--  Shell  --------------------------------------------------------------------

def run_command (com, *args, value='', silent=False, color=None):
    '''
    Unless silent=True, prints incrementally.
    @arg value - '', 'v', 'vo', 'o'.
    Unless 'v', signals an error for nonzero status.

     * Returns (value, output) if 'vo'.
     * Returns value if 'v'.
     * Returns output if 'o'.

    '''
    if color is None:
        return _run_command1(com, args, value, silent)
    else:
        with _stdout_color(color):
            return _run_command1(com, args, value, silent)

def _run_command1 (com, args, value, silent):
    if 'o' in value: output = bytearray()
    (pid, fd) = pty.fork()
    if pid == 0:
        os.execlp(com, com, *args)
    else:
        if not silent: os.write(1, b'\033[36m')
        while True:
            b = _read(fd, 64)
            if not b: break
            if not silent: os.write(1, strip_escapes(b))
            if 'o' in value: output.extend(b)
        if not silent: os.write(1, b'\033[39m')
        status = os.waitpid(pid, 0)[1]
        if not ('v' in value or status == 0):
            raise Exception('Executable error: %s' % status)
        if 'o' in value:
            output = output.decode('raw_unicode_escape')
        if value == 'vo': return (status, output)
        elif value == 'v': return status
        elif value == 'o': return output

def _read (fd, bufsize):
    b = b''
    try:
        b = os.read(fd, bufsize)
    except OSError:
        pass
    return b

##  Stdout color.
class _stdout_color (object):
    ##  Constructor.
    def __init__ (self, color):
        colors = {'red': b'\033[31m',
                  'green': b'\033[32m',
                  'yellow': b'\033[33m',
                  'blue': b'\033[34m',
                  'magenta': b'\033[35m',
                  'cyan': b'\033[36m'}
        ##  The escape code for the given color.
        self.color = colors[color]
    ##  Enter.
    def __enter__ (self):
        os.write(1, self.color)
    ##  Exit.
    def __exit__ (self, t, v, tb):
        os.write(1, b'\033[39m')


def _is_digit_or_semicolon (x):
    return (48 <= x <= 57 or x == 59)

def _is_letter (x):
    return (65 <= x <= 90 or 97 <= x <= 122)

# returns end point if looking at xterm escape sequence, -1 otherwise

def _escape_seq (b, i):
    if not (i < len(b) and b[i] == 27): return -1
    i += 1
    if not (i < len(b) and b[i] == 91): return i
    i += 1
    while i < len(b) and _is_digit_or_semicolon(b[i]): i += 1
    if i < len(b) and _is_letter(b[i]): i += 1
    return i

def strip_escapes (b):
    '''
    Strips out any xterm escape sequences, such as color changes.
    '''
    out = None
    i = k = 0
    while k < len(b):
        j = _escape_seq(b,k)
        if j < 0:
            k += 1
        else:
            if out is None: out = bytearray(b[:k])
            else: out.extend(b[i:k])
            i = k = j
    if i < len(b) and out is not None:
        out.extend(b[i:])
    if out is None: return b
    else: return out


#--  More  ---------------------------------------------------------------------

##  A pager.
class _Pager (object):

    ##  Constructor.
    def __init__ (self, pagesize=40):
        ##  The page size, in lines.
        self.pagesize = pagesize

    ##  Call it.
    def __call__ (self, iter):
        for i,x in enumerate(iter):
            if i > 0 and i % self.pagesize == 0:
                if input() == 'q': break
            print(x)

more = _Pager()
'''
Prints a "page" at a time and waits for space bar or 'q'.
'''

#--  Command line processing, v5  ----------------------------------------------

##  Process command-line arguments.

class Shift (object):
    '''
    Low-level command-line processing.
    '''

    ##  Constructor.  The argv should not include the command, only the arguments.

    def __init__ (self, argv=sys.argv, offset=1):
        self._usage = ''

        ##  The command line.
        self.argv = argv

        ##  Current pointer into argv.
        self.ac = 0

        self._initial_offset = offset

    ##  Set the usage message.

    def set_usage (self, msg):
        if len(self.argv) > 1 and self.argv[1] in ('-?', '--help'):
            print(msg)
            sys.exit(0)
        self._usage = msg

    ##  Print usage.

    def print_usage (self):
        if self._usage:
            print('USAGE:', file=sys.stderr)
            print(self._usage, file=sys.stderr)
        else:
            print('No usage information available', file=sys.stderr)

    ##  Begin processing.

    def __enter__ (self):
        self.ac = self._initial_offset
        return self

    ##  Calls done().

    def __exit__ (self, t, b, tb):
        if t is None:
            self.done()

    ##  Print out an error message, including usage, and quit.

    def error (self, msg):
        print('**', msg, file=sys.stderr)
        self.print_usage()
        sys.exit(1)

    ##  Whether any more arguments remain.

    def peek (self, targ=None):
        if targ is None:
            if self.ac < len(self.argv):
                return self.argv[self.ac]
        else:
            return (self.ac < len(self.argv) and self.argv[self.ac] == targ)

    ##  Whether the next argument is a flag.

    def isflag (self):
        return self.ac < len(self.argv) and self.argv[self.ac].startswith('-')

    ##  If the next argument is a flag, return it and advance.

    def flag (self):
        if self.isflag():
            return self()

    ##  Return the next argument and advance.

    def __call__ (self, targ=None):
        if targ is None:
            if self.ac >= len(self.argv):
                self.error('Too few arguments')
            arg = self.argv[self.ac]
            self.ac += 1
            return arg
        elif self.ac < len(self.argv) and self.argv[self.ac] == targ:
            self.ac += 1
            return True
        else:
            return False

    ##  Return the next argument and advance, if there is a next argument.

    def ifable (self):
        if self.ac < len(self.argv):
            arg = self.argv[self.ac]
            self.ac += 1
            return arg

    ##  Returns True just in case __call__ will succeed.

    def able (self):
        return self.ac < len(self.argv)

    ##  Whether or not we have processed all arguments.

    def isdone (self):
        return self.ac >= len(self.argv)

    ##  Return the remaining arguments as a list, and advance to the end.

    def rest (self):
        args = self.argv[self.ac:]
        self.ac = len(self.argv)
        return args
    
    ##  Check whether all arguments have been consumed.  Signal an error if not.

    def done (self):
        if self.ac != len(self.argv):
            self.error('Too many arguments')


shift = Shift(sys.argv[1:])
'''
An instance of Shift reading sys.argv[1:].
'''


#--  Main  ---------------------------------------------------------------------

def _docstring_lines (x):
    doc = x.__doc__
    if doc:
        if doc.startswith('\n'):
            i = 1
            while i < len(doc) and doc[i].isspace() and doc[i] not in '\r\n':
                i += 1
            prefix = doc[1:i]
            doc = doc[i:]
        else:
            prefix = ''
        n = len(prefix)
        for line in doc.split('\n'):
            if line.startswith(prefix):
                line = line[n:]
            yield line


class Main (object):
    '''
    A command-line processor. Define a class that specializes this one. Any methods
    it has whose names begin with ``com_`` are taken to represent command-line commands.
    All remaining arguments are passed as positional arguments, and any flags are passed 
    as keyword arguments. For example, ``foo -v -n=moo bar baz`` translates to a call
    ``self.com_foo('bar', 'baz', v=True, n='moo')``.
    '''

    def _usage_message (self):
        yield 'Usage: COMMAND [-FLAG[=VAL]*] [ARG*]'

        if self.__doc__:
            yield ''
            for line in _docstring_lines(self):
                yield line

        yield ''
        yield 'Commands:'
        for name in dir(self):
            if name.startswith('com_'):
                yield ''
                com = name[4:]
                method = getattr(self, name)
                dflts = method.__defaults__ or []
                nkws = len(dflts)
                varnames = method.__code__.co_varnames
                nargs = method.__code__.co_argcount - (1 + nkws)  # -1 for self
                i = 1          # first is self
                j = 1 + nargs
                k = j + nkws   # after kws are local variables
                args = varnames[i:j]
                kws = varnames[j:k]
                words = [com]

                # print('** name=', name)
                # print('   dflts=', dflts, 'varnames=', varnames, 'nargs=', nargs, 'nkws=', nkws)
                # print('   kws=', kws, 'args=', args, 'i=', i, 'j=', j, 'k=', k)

                words.extend(args)
                yield '  ' + ' '.join(words)

                if kws:
                    for (i, kw) in enumerate(kws):
                        yield '      -' + kw + ' default: ' + repr(dflts[i])
                
                if method.__doc__:
                    for line in _docstring_lines(method):
                        yield '    ' + line

    def __call__ (self, comline=None):
        if comline is None:
            args = sys.argv
        else:
            args = [None] + comline.split()

        with Shift(args) as shift:
            shift.set_usage('\n'.join(self._usage_message()))
            args = []
            while not (shift.isdone() or shift.isflag()):
                args.append(shift())
            kwargs = {}
            while shift.isflag():
                flag = shift()
                key = flag[1:]
                i = key.find('=')
                value = True
                if i >= 0:
                    value = key[i+1:]
                    key = key[:i]
                kwargs[key] = value
            args.extend(shift.rest())
    
        com = None
        nwords = 0
        if not args:
            print('** No command given')
            sys.exit(1)
        for n in range(1, len(args)+1):
            methodname = 'com_' + '_'.join(args[:n])
            if hasattr(self, methodname):
                com = getattr(self, methodname)
                nwords = n
        if com is None:
            print('** Not a command:', args[0])
            sys.exit(1)
        args = args[nwords:]
        com(*args, **kwargs)


#--  Timeout  ------------------------------------------------------------------

class TimedOut (Exception):
    '''
    Exception used when a timeout occurs.
    '''
    pass


class Timeout (object):
    '''
    Runs a timer.
    '''

    ##  Constructor.

    def __init__ (self, nsecs):

        ##  How long before the alarm goes off.
        self.nsecs = nsecs

        ##  The timer, in another thread, while running.
        self.timer = None

    ##  Enter.  Starts a timer in a thread.  If the timer goes off before
    #   it is canceled, it raises a TimedOut exception.

    def __enter__ (self):
        self.timer = threading.Timer(self.nsecs, self._alarm)

    def _alarm (self):
        raise TimedOut()

    ##  Exit.  Cancel the timer.  If TimedOut is raised, pass it through.

    def __exit__ (self, t, v, tb):
        self.timer.cancel()
        if t == TimedOut:
            return True


#--  Elapsed Time  -------------------------------------------------------------

class Timer (object):
    '''
    Prints out as elapsed time since it was created.
    '''
    
    ##  Constructor.

    def __init__ (self):

        ##  The start time.
        self.start = time()

    def elapsed (self):
        return time() - self.start

    ##  Prints elapsed time.

    def __str__ (self):
        return elapsed_time_str(self.start, time())


#--  Progress Monitor  ---------------------------------------------------------

class Progress (object):
    '''
    A progress monitor.
    '''

    ##  Constructor.

    def __init__ (self, n=None):

        ##  How many ticks are expected in total.  It's OK if it's an underestimate.
        self.target = n

        ##  How many ticks have already taken place.
        self.count = 0

        ##  To keep track of elapsed time.
        self.timer = Timer()

        self.last_t = None

    def __enter__ (self):
        return self

    def done (self):
        self.printout(end='\n')

    def __exit__ (self, t, v, tb):
        self.done()

    ##  Increment by n ticks (default 1).  Prints/updates a progress message.

    def __iadd__ (self, n=1):
        self.count += n
        t = time()
        if self.last_t is None or t - self.last_t > 0.3:
            self.last_t = t
            self.printout()
        return self

    def printout (self, end=' '):
        if self.target is None:
            print('\rProgress: %d' % self.count,
                  'Time elapsed: %s' % self.timer,
                  end=end,
                  file=sys.stderr)
            sys.stderr.flush()

        else:
            proportion_done = self.count/float(self.target)
            elapsed = self.timer.elapsed()
            est_total = elapsed/proportion_done
            print('\rProgress: %d/%d (%2.2f%%)' % (self.count, self.target, 100 * proportion_done),
                  'Time remaining: %s' % elapsed_time_str(elapsed, est_total),
                  end=end,
                  file=sys.stderr)
            sys.stderr.flush()



#--  Manifest  -----------------------------------------------------------------
#
#  A manifest is a listing of the files in a directory tree.  The entries are of
#  form:
#
#      name relpath size [modtime] [hash]
#
#  Options.  By default, all are False:
#
#      symlinks=True:  Follow symlinks.  Signal an error for dangling symlinks
#                      or symlink chains.  If symlinks=False, the entry for a
#                      symlink has the target's name in place of size.
#
#      tmpfiles=True:  Include tmp files.  Tmp file patterns: *~ #*# tmp tmp.* *.tmp
#
#      downcase=True:  Downcase all names.  I.e., case-insensitive matching.
#
#      modtimes=True:  Include modtimes in the output.
#
#      hashes=True:    Include SHA5 hash values in the output.
#

# def manifest (dir, symlinks=False, tmpfiles=False, downcase=False, hashes=False):
#     return sorted(iter_tree(dir, symlinks, tmpfiles))
# 
# def iter_tree (dir, symlinks=False, tmpfiles=False, downcase=False, hashes=False):
#     names = os.listdir(dir)
#     for name in names:
#         fn = os.path.join(dir, name)
#         islink = False
#         size = None
#         modtime = None
#         hash = None
#         if os.path.islink(fn):
#             islink = True
#             tgt = os.readlink(fn)
#             if symlinks:
#                 if not os.path.exists(tgt):
#                     raise Exception('Dangling symlink: %s -> %s' % (fn, tgt))
#                 if os.path.islink(tgt):
#                     raise Exception('Symlink chain: %s -> %s' % (fn, tgt))
#                 fn = tgt
#                 islink = False
#             else:
#                 size = tgt
#         if not islink:
#             if os.path.isdir(fn):
#                 for entry in iter_tree(fn):
#                     yield entry
#                 continue
#             else:
#                 size = file_size(fn)
#                 
