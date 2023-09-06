
import sys, subprocess
from time import time
from selkie.string import elapsed_time_str


#--  file_size  ----------------------------------------------------------------

##  Returns the file size in bytes.

def file_size (fn):
    return os.stat(fn).st_size


#--  System calls  -------------------------------------------------------------

##  Make a synchronous call, raising an exception on failure.
#   If the call is unsuccessful, an exception is raised.
#   There is no return value.

# def call (program, *args):
#     value = os.spawnvp(os.P_WAIT, program, [program] + list(args))
#     if value != 0:
#         raise Exception("Program failed: value " + str(value) + ": " + program + " " + ' '.join(args))

##  Makes an asynchronous call, returning 0 on success and an error code on failure.

# def launch (program, *args):
#     return os.spawnvp(os.P_NOWAIT, program, [program] + list(args))


def system (*args, silent=False):
    return True if subprocess.run(args, capture_output=silent).returncode == 0 else False

# return value has members returncode, stdout, stderr

def backtick (*args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


#--  Shell  --------------------------------------------------------------------

##  Prints output all at once, not incrementally.

def shell (cmd):
    print(subprocess.getoutput(cmd))

##  Unless silent=True, prints incrementally.
#   @arg value - '', 'v', 'vo', 'o'.
#   Unless 'v', signals an error for nonzero status.
#    - Returns (value, output) if 'vo'.
#    - Returns value if 'v'.
#    - Returns output if 'o'.

def run_command (com, *args, value='', silent=False, color=None):
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

##  Strip xterm escape sequences, e.g. color changes.

def strip_escapes (b):
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

##  Prints a "page" at a time and waits for space bar or 'q'.
more = _Pager()


#--  Command line processing, v1  ----------------------------------------------

##  Deprecated.  Use shift instead.

class CommandLine (object):

    ##  Constructor.

    def __init__ (self, usage, nargs=None):
        self.__usage = usage
        ##  Arg vector.
        self.argv = sys.argv
        ##  Current position.
        self.i = 1
        ##  Command.
        self.arg0 = None
        ##  Number of arguments.
        self.nargs = nargs

    ##  Print usage and exit.
    def usage (self):
        sys.stderr.write('Usage: %s\n' % self.__usage)
        sys.exit(1)

    ##  Whether the current argument is a flag.
    def has_option (self):
        if len(self.argv) > self.i and self.argv[self.i][0] == '-':
            return True
        else:
            return False

    ##  Get the value for opt.
    def option (self, opt):
        if len(self.argv) <= self.i or self.argv[self.i][0] != '-':
            raise Exception('No option')
        key = self.argv[self.i]
        self.i += 1
        return key

    ##  Check whether the number of arguments is correct.
    def check_nargs (self):
        if self.arg0 is None:
            self.arg0 = self.i
            if self.nargs is None:
                self.nargs = len(self.argv) - self.arg0
            elif len(self.argv) - self.arg0 > self.nargs:
                self.usage()

    ##  Iterator method.
    def __next__ (self):
        self.check_nargs()
        t = self.i - self.arg0
        if t >= self.nargs:
            raise StopIteration
        if t < len(self.argv):
            arg = self.argv[t]
        else:
            arg = ''
        self.i += 1
        return arg

    ##  Get the i-th argument.
    def __getitem__ (self, i):
        self.check_nargs()
        if i < 0 or i >= self.nargs: raise IndexError
        t = self.arg0 + i
        if t < len(self.argv):
            return self.argv[t]
        else:
            return ''

    ##  Get the number of arguments.
    def __len__ (self):
        self.check_nargs()
        return self.nargs

    ##  Returns self.
    def __iter__ (self):
        return self


#--  Command line processing, v2  ----------------------------------------------

def _n_oblig_params (fnc):
    nparams = fnc.__code__.co_argcount
    nopt = len(fnc.__defaults__)
    return nparams - nopt

def _optional_params (fnc):
    nparams = fnc.__code__.co_argcount
    nopt = len(fnc.__defaults__)
    noblig = nparams - nopt
    names = fnc.__code__.co_varnames
    return names[noblig:nparams]

##  Deprecated.  Use shift instead.

def run_main_2 (main):
    if len(sys.argv) > 1 and sys.argv[1] == '-?': _print_usage(main)
    show_stack_trace = False
    kwargs = {}
    noblig = _n_oblig_params(main)
    i = 1 + noblig
    if i > len(sys.argv): _print_usage(main)
    while i < len(sys.argv):
        arg = sys.argv[i]
        i += 1
        if arg == '-!': show_stack_trace = True
        elif arg == '--': break
        else:
            k = arg.find('=')
            if k >= 0:
                key = arg[1:k]
                value = arg[k+1:]
            else:
                key = arg[1:]
                value = '1'
            if key in kwargs:
                print("Flag '-%s' multiply specified" % key, file=sys.stderr)
                sys.exit(1)
            kwargs[key] = value

    args = sys.argv[i:]
    try:
        value = main(*args, **kwargs)
        if value is not None:
            print(value)
        sys.exit(0)
    except Exception as e:
        if show_stack_trace:
            traceback.print_exc()
        else:
            print('ERROR:', e, file=sys.stderr)
        sys.exit(1)


#--  Command line processing, v3  ----------------------------------------------

##  Deprecated.  Use shift instead.

def run_main (main):
    show_stack_trace = False
    kwargs = {}
    i = 1
    while i < len(sys.argv) and sys.argv[i].startswith('-'):
        arg = sys.argv[i]
        i += 1
        if arg == '-?': _print_usage(main)
        elif arg == '-!': show_stack_trace = True
        elif arg == '--': break
        else:
            k = arg.find('=')
            if k >= 0:
                key = arg[1:k]
                value = arg[k+1:]
            else:
                key = arg[1:]
                value = '1'
            if key in kwargs:
                print("Flag '-%s' multiply specified" % key, file=sys.stderr)
                sys.exit(1)
            kwargs[key] = value

    args = sys.argv[i:]
    try:
        value = main(*args, **kwargs)
        if value is not None:
            print(value)
        sys.exit(0)
    except Exception as e:
        if show_stack_trace:
            traceback.print_exc()
        else:
            print('ERROR:', e, file=sys.stderr)
        sys.exit(1)

def _print_usage (f):
    progname = sys.argv[0]
    nargs = f.__code__.co_argcount
    defaults = f.__defaults__
    nopt = len(defaults)
    noblig = nargs - nopt
    allow_xs_positional = (f.__code__.co_flags & 0x04)
    allow_xs_keywords = (f.__code__.co_flags & 0x08)
    varnames = f.__code__.co_varnames
    oblig = varnames[:noblig]
    opt = varnames[noblig:nargs]
    words = [progname] + list(oblig)
    if opt: words.append('[%s]' % ' '.join(opt))
    print('USAGE:   ', ' '.join(words))
    if defaults:
        print('Defaults:')
        for i in range(nopt):
            print('    %-10s %s' % (opt[i], defaults[i]))
    print('Flags:')
    print('    Any arg can be provided as a flag in form -arg=value')
    print('    -arg  is the same as -arg=1')
    print('    -?    prints this usage message')
    print('    -!    causes a stack trace to be printed in case of error')
    print('    --    terminates flags; what follows are positional arguments')
    if f.__doc__:
        print()
        print(f.__doc__)
    sys.exit(1)


#--  Command line processing, v4  ----------------------------------------------

def _print_boilerplate ():
    print('Optional arguments may be specified in any of three ways:')
    print(' - include them among the positional arguments')
    print(' - in flag form, before the positional arguments')
    print(' - in keyword form, after the positional arguments')
    print()
    print('However, optional arguments that are specified as keyword-only')
    print('cannot be provided positionally.')
    print()
    print('Flags (precede positional arguments):')
    print('    -?         prints this usage message')
    print('    -!         causes a stack trace to be printed in case of error')
    print('    -ARG       value is 1')
    print('    --ARG      value is 1')
    print('    -ARG=VAL')
    print('    --ARG=VAL')
    print('    --         terminates flags')
    print()
    print('Keyword arguments have the form KEY=VAL and follow the positional')
    print('arguments.')


##  Dispatch table.

class _DispatchTable (object):

    ##  Constructor.

    def __init__ (self, table):
        ##  Contents.
        self.table = table
        
    ##  Get value.
    def __getitem__ (self, name):
        if name in self.table:
            return self.table[name]
        else:
            self.error('Unrecognized command: %s' % name)
        
    ##  Print usage and exit.
    def usage (self):
        print('Commands:')
        for name in sorted(self.table):
            print()
            f = _Function(name, self.table[name])
            f.print_description()
        print()
        _print_boilerplate()
        sys.exit(1)
        
    ##  Print error and usage and exit.
    def error (self, msg):
        print('**', msg, file=sys.stderr)
        self.usage()


##  A function.
class _Function (object):

    ##  Constructor.
    def __init__ (self, name, f):

        ##  The name.
        self.name = name

        ##  The python function.
        self.func = None

        ##  Whether it has a 'self' argument.
        self.selfarg = None

        ##  Number of positional parameters.
        self.npos = None

        ##  Number of obligatory parameters.
        self.nobl = None

        ##  Number of optional parameters.
        self.nopt = None

        ##  Number of keyword parameters.
        self.nkwo = None

        ##  Total number of arguments.
        self.nargs = None

        ##  Whether it has a '*args' parameter.
        self.star = None

        ##  Whether it has a '**kwargs' parameter.
        self.starstar = None

        ##  Names of parameters.
        self.names = None

        ##  Default values for parameters.
        self.defaults = None

        ##  Whether it accepts keyword arguments.
        self.keywords = None

        if hasattr(f, '__code__'):
            self.func = f
            self.selfarg = None
        elif hasattr(f, '__call__'):
            m = f.__call__
            if not (hasattr(m, '__self__') and hasattr(m, '__func__')):
                raise Exception('Not a recognized function type')
            self.func = f = m.__func__
            self.selfarg = m.__self__

        self.npos = f.__code__.co_argcount
        if f.__defaults__:
            self.nopt = len(f.__defaults__)
        else:
            self.nopt = 0
        self.nobl = self.npos - self.nopt
        self.nkwo = f.__code__.co_kwonlyargcount
        self.nargs = self.npos + self.nkwo
        self.star = bool(f.__code__.co_flags & 0x04)
        self.starstar = bool(f.__code__.co_flags & 0x08)

        self.names = f.__code__.co_varnames

        if self.selfarg:
            self.npos -= 1
            self.nobl -= 1
            self.nargs -= 1
            self.names = self.names[1:]

        self.defaults = []
        if f.__defaults__: self.defaults.extend(f.__defaults__)
        if self.nkwo:
            for name in self.names[self.npos:self.nargs]:
                self.defaults.append(f.__kwdefaults__[name])

        if self.starstar:
            self.keywords = True
        else:
            self.keywords = set(self.names[self.nobl : self.nargs])

    ##  Whether it accepts kw as a keyword argument.

    def accepts_keyword (self, kw):
        return self.keywords is True or kw in self.keywords

    ##  Print out a description.

    def print_description (self):
        args = ' '.join(self.names[:self.nobl])
        if self.nopt > 0:
            args = '%s [%s]' % (args, ' '.join(self.names[self.nobl:self.npos]))
        print(self.name, args)
        if self.star:
            print('    Additional positional arguments are allowed')
        if self.nkwo > 0:
            print('    Keyword only: ' + ' '.join(self.names[self.npos:self.nargs]))
        if self.defaults:
            print('    Defaults:')
            for i in range(self.nobl, self.nargs):
                print('        %-10s %s' % (self.names[i], self.defaults[i-self.nobl]))
        if self.starstar:
            print('    Additional keyword arguments are allowed')
        if self.func.__doc__:
            print()
            print(self.func.__doc__)

    ##  Print an error message, print usage, and exit.

    def error (self, msg):
        print('**', msg, file=sys.stderr)
        self.usage()
        
    ##  Print usage and exit.

    def usage (self):
        self.print_description()
        print()
        _print_boilerplate()
        sys.exit(1)

    ##  Call the function.

    def __call__ (self, args, kwargs, stack_trace):
        try:
            if self.selfarg: args = [self.selfarg] + args
            value = self.func(*args, **kwargs)
            if value is not None:
                print(value)
            sys.exit(0)
        except Exception as e:
            if stack_trace:
                traceback.print_exc()
            else:
                print('ERROR:', e, file=sys.stderr)
            sys.exit(1)


##  Dispatches either to a DispatchTable or to a Function.

class _Form (object):

    ##  Constructor.  Only one of 'table' or 'function' get set.
    def __init__ (self, main):

        ##  The DispatchTable.
        self.table = None
        ##  The Function.
        self.function = None
        ##  Positional arguments.
        self.args = None
        ##  Keyword arguments.
        self.kwargs = None
        ##  Whether to show a stack trace on error.
        self.stack_trace = None

        if isinstance(main, dict):
            self.table = _DispatchTable(main)
            self.function = None
        else:
            self.table = None
            self.function = _Function(sys.argv[0], main)
        self.args = []
        self.kwargs = {}
        self.stack_trace = False

    ##  The number of optional arguments.
    def n_optional_args (self):
        return self.function.nopt

    ##  The number of obligatory arguments.
    def n_obligatory_args (self):
        return self.function.nobl

    ##  Add arguments.
    def add_args (self, args):
        self.args.extend(args)

    ##  Add a keyword arg.
    def add_keyword_arg (self, key, value):
        if self.function.accepts_keyword(key):
            if key in self.kwargs:
                self.error('Keyword specified multiple times: %s' % key)
            self.kwargs[key] = value
        else:
            self.error('Unrecognized keyword: %s' % key)

    ##  Call the function on arguments and keyword arguments.
    def eval (self):
        self.function(self.args, self.kwargs, self.stack_trace)

    ##  Print an error message, print usage, and exit.
    def error (self, msg):
        if self.function: self.function.error(msg)
        else: self.table.error(msg)

    ##  Print usage and exit.
    def usage (self):
        if self.function: self.function.usage()
        else: self.table.usage()


def _isflag (i):
    return i < len(sys.argv) and sys.argv[i].startswith('-') and sys.argv[i] != '-'

def _isnonflag (i):
    return i < len(sys.argv) and ((not sys.argv[i].startswith('-')) or sys.argv[i] == '-')


##  Deprecated.  A command-line parser.
class _CommandLineParser (object):

    ##  Constructor.

    def __init__ (self):

        ##  Beginning of obligatory args.
        self.i = None
        ##  Beginning of optional args.
        self.j = None
        ##  Beginning of keyword args.
        self.k = None

    ##  Call it.
    def __call__ (self, main):
        form = _Form(main)
        self.i = 1
        while self.special_flag(form): pass
        if form.function is None: self.command(form)
        self.flags(form)
        self.obligatory_args(form)
        self.keyword_args(form)
        self.optional_args(form)
        return form

    ##  Whether a special flag has been provided (-? or -!).
    def special_flag (self, form):
        if self.i >= len(sys.argv): return False
        arg = sys.argv[self.i]
        if arg == '-!': form.stack_trace = True
        elif arg == '-?': form.usage()
        else: return False
        self.i += 1
        return True

    ##  Set the command.
    def command (self, form):
        self.i = 1
        if _isnonflag(self.i):
            name = sys.argv[self.i]
            com_name = '%s %s' % (sys.argv[0], name)
            self.i += 1
            form.function = _Function(name, form.table[name])
        else:
            form.error('No command provided')

    ##  Process flags.
    def flags (self, form):
        while _isflag(self.i):
            if not self.special_flag(form):
                arg = sys.argv[self.i]
                self.i += 1
                if arg == '--': break
                t = arg.find('=')
                if t < 0:
                    flag = arg[1:]
                    value = '1'
                else:
                    u = 1
                    if arg[u] == '-': u += 1
                    flag = arg[u:t]
                    value = arg[t+1:]
                form.add_keyword_arg(flag, value)

    ##  Process obligatory args.
    def obligatory_args (self, form):
        self.j = self.i + form.n_obligatory_args()
        if self.j > len(sys.argv):
            form.error('Not enough arguments provided')
        form.add_args(sys.argv[self.i:self.j])

    ##  Process keyword args.
    def keyword_args (self, form):
        self.k = len(sys.argv)
        while self.k > self.j:
            arg = sys.argv[self.k-1]
            t = arg.find('=')
            if t < 0: break
            self.k -= 1
            (key,value) = (arg[:t], arg[t+1:])
            form.add_keyword_arg(key, value)
        
    ##  Process optional args.
    def optional_args (self, form):
        if self.k - self.j > form.n_optional_args():
            form.error('Too many arguments provided')
        form.add_args(sys.argv[self.j:self.k])


_command_line = None

##  Deprecated.  Use shift instead.

def error (msg=None):
    global _command_line
    if _command_line is None:
        raise Exception('Cannot be called except in the context of run')
    _command_line.error(msg)

##  Deprecated.  Use shift instead.

def run (main):
    global _command_line
    p = _CommandLineParser()
    _command_line = p(main)
    _command_line.eval()


#--  Command line processing, v5  ----------------------------------------------

##  Process command-line arguments.

class Shift (object):

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


##  An instance of Shift reading sys.argv[1:].
shift = Shift(sys.argv[1:])


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

##  Exception used when a timeout occurs.

class TimedOut (Exception): pass

##  Runs a timer.

class Timeout (object):

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


# class Timeout (object):
# 
#     def __init__ (self, nsecs, ontimeout=None):
#         self.nsecs = nsecs
#         self.ontimeout = None
# 
#     def __enter__ (self):
#         signal.signal(signal.SIGALRM, self._alarm)
#         signal.alarm(self.nsecs)
# 
#     def _alarm (self, signo, frame):
#         raise TimedOut()
# 
#     def __exit__ (self, t, v, tb):
#         signal.alarm(0)
#         signal.signal(signal.SIGALRM, signal.SIG_DFL)
#         if t == TimedOut:
#             return True

#  This works, but very heavyweight and clunky!!
#  Requires one to communicate with body via files or pipes!!
#
# class with_timeout (object):
# 
#     def __init__ (self, nsecs, fnc, *args, **kwargs):
#         self.childpid = None
#         self.timedout = False
# 
#         self.childpid = os.fork()
# 
#         # child
#         if self.childpid == 0:
#             fnc(*args, **kwargs)
#             os.kill(os.getpid(), SIGTERM)
# 
#         # parent
#         else:
#             timer = threading.Timer(nsecs, self._alarm)
#             timer.start()
#             (pid, status) = os.wait()
#             if not self.timedout:
#                 timer.cancel()
# 
#     def _alarm (self):
#         os.kill(self.childpid, SIGTERM)
#         self.timedout = True


#  Threading doesn't work.  Threads can't be interrupted, and even the
#  main thread doesn't always response to interrupt_main().
# 
# def _timer_goes_off ():
#     from seal.app.log import DEBUG
#     DEBUG('timer goes off')
#     interrupt_main()
# 
# class Timeout (object):
# 
#     def __init__ (self, nsecs, ontimeout=None):
#         self.timer = None
#         self.nsecs = nsecs
#         self.ontimeout = ontimeout
# 
#     def __enter__ (self):
#         self.timer = threading.Timer(self.nsecs, _timer_goes_off)
#         from seal.app.log import DEBUG
#         DEBUG('** starting timer, nsecs=', self.nsecs, 'thread=', repr(threading.current_thread()))
#         self.timer.start()
# 
#     def __exit__ (self, t, v, tb):
#         from seal.app.log import DEBUG
#         DEBUG('** cancelling timer', 't=', t)
#         self.timer.cancel()
#         if t == KeyboardInterrupt:
#             DEBUG('** got an interrupt')
#             if self.ontimeout is not None:
#                 self.ontimeout()
#             # suppress the exception
#             return True


#--  Elapsed Time  -------------------------------------------------------------

##  Prints out as elapsed time since it was created.

class Timer (object):

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

##  A progress monitor.

class Progress (object):

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


#--  Load module  --------------------------------------------------------------

##  Load a module, given a fully qualified name.

def load_module (name):
    names = name.split('.')
    module = file = path = None
    try:
        for name in names:
            (file, path, desc) = imp.find_module(name, path)
            module = imp.load_module(name, file, path, desc)
            if file is not None: file.close()
            if hasattr(module, '__path__'): path = module.__path__
    finally:
        if file is not None: file.close()
    return module

##  Import a class, given a fully qualified name.

def import_class (spec):
    i = spec.rfind('.')
    if i < 0: raise Exception('Need a fully qualified class name: %s' % spec)
    name = spec[i+1:]
    modname = spec[:i]
    module = importlib.import_module(modname)
    try:
        cls = module.__dict__[name]
    except KeyError:
        raise Exception('No class named %s in %s' % (name, modname))
    return cls

##  The fully qualified name for a given class.

def class_name (cls):
    return cls.__module__ + '.' + cls.__name__


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


#--  XTerm  --------------------------------------------------------------------

##  Dict mapping color names to escape strings.
fg = {'black': '\033[30m',
      'red': '\033[31m',
      'green': '\033[32m',
      'yellow': '\033[33m',
      'blue': '\033[34m',
      'magenta': '\033[35m',
      'cyan': '\033[36m',
      'white': '\033[37m',
      'default': '\033[39m'}

##  Dict mapping color names to escape strings.
bg = {'black': '\033[40m',
      'red': '\033[41m',
      'green': '\033[42m',
      'yellow': '\033[43m',
      'blue': '\033[44m',
      'magenta': '\033[45m',
      'cyan': '\033[46m',
      'white': '\033[47m',
      'default': '\033[49m'}

##  Returns a string that displays the contents in black.
def black (s):
    return fg['black'] + s + fg['default']

##  Returns a string that displays the contents in red.
def red (s):
    return fg['red'] + s + fg['default']

##  Returns a string that displays the contents in green.
def green (s):
    return fg['green'] + s + fg['default']

##  Returns a string that displays the contents in yellow.
def yellow (s):
    return fg['yellow'] + s + fg['default']

##  Returns a string that displays the contents in blue.
def blue (s):
    return fg['blue'] + s + fg['default']

##  Returns a string that displays the contents in magenta.
def magenta (s):
    return fg['magenta'] + s + fg['default']

##  Returns a string that displays the contents in cyan.
def cyan (s):
    return fg['cyan'] + s + fg['default']

##  Returns a string that displays the contents in white.
def white (s):
    return fg['white'] + s + fg['default']

##  An escape string that moves the cursor n spaces to the right.
def cursor_right (n=1):
    return '\033%dC' % n

##  An escape string that moves the cursor n spaces to the left.
def cursor_left (n=1):
    return '\033%dD' % n

##  An escape string that moves the cursor to column n.
def goto_column (n):
    return '\033%dG' % n
