##  @package seal.app.log
#   Provides the Logger class.

import random, sys, traceback
from io import StringIO
from os.path import expanduser
from seal.core.io import pprint, PPrinter


##  Create a logger from a Config or dict.
#   Reads keys 'log_file' and 'logging'.

def logger_from_config (cfg):
    return Logger(cfg.get('log_file', '-'), cfg.get('logging', 'all'))


##  Global variable, used by DEBUG.  This gets set when the Logger is put
#   in a with-statement.

LOG = None

##  Unconditionally write a log message to LOG.

def DEBUG (*args, **kwargs):
    global LOG
    LOG(True, *args, **kwargs)


#--  Logger  -------------------------------------------------------------------

##  Logger.  Conditionally prints log messages.

class Logger (object):

    ##  Constructor.

    def __init__ (self, filename=None, conds=None, copy_of=None):
        if copy_of is None:
            if filename == '-': filename = None
            elif isinstance(filename, str): filename = expanduser(filename)
    
            ##  A random 6-digit int used to identify this Logger.
            self.id = '%06d' % random.randrange(1000000)

            ##  The log file's filename.  If writing to stdout, it is '-'.
            self.filename = filename

            ##  The list of active conditions.
            self.conds = None

            ##  If True, ignore the conditions and print unconditionally.
            #   If False, ignore the conditions and do not print at all.
            #   If None, use the conditions to decide.
            self.uncond = None

            ##  A stream writing to the log file.
            self.file = None

            ##  A version of pprint that invokes me.
            self.pprint = pprint

            self._value = None
            self._on_exit = None
    
            if isinstance(conds, bool):
                self.uncond = conds
            elif conds is None:
                self.uncond = True
            else:
                if isinstance(conds, str):
                    conds = [c.strip() for c in conds.split(',')]
                self.set_conds(conds)

        else:
            self.id = copy_of.id
            self.filename = copy_of.filename
            self.conds = copy_of.conds
            self.uncond = copy_of.uncond
            self.file = None
            self.pprint = pprint
            self._value = None
            self._on_exit = None

    ##  Create a copy.

    def dup (self):
        return Logger(copy_of=self)

    ##  Set the logging conditions.  Calls the set() method on each in turn.

    def set_conds (self, conds):
        self.conds = set()        
        if isinstance(conds, str):
            self.set(conds)
        else:
            for cond in conds:
                self.set(cond)

    ##  Sets filename and calls set_conds().

    def configure (self, log_file=None, logging=None):
        if log_file is not None:
            self.filename = log_file
        if logging is not None:
            self.set_conds(logging)

    ##  Whether the condition is active.
    #    - Returns False if there is no open file.
    #    - Returns False if self.uncond is False (as opposed to None).
    #    - Returns True if cond is True.
    #    - Returns True if self.uncond is True.
    #    - Otherwise, returns True/False depending on whether cond is in self.conds.

    def on (self, cond):
        return (self.file is not None and
                self.uncond is not False and
                (cond is True or self.uncond or cond in self.conds))

    ##  Put name into self.conds.  Also activate all conditions implied by this one.
    #    - 'all' sets self.uncond to True.
    #    - 'off' sets self.uncond to False.
    #    - 'traceback' implies 'error'.
    #    - 'trace' implies 'path'.
    #    - 'path' implies 'req'.

    def set (self, name):
        if name not in self.conds:
            self.conds.add(name)
            if name == 'all':
                self.uncond = True
            elif name == 'off':
                self.uncond = False
            elif name == 'traceback':
                self.set('error')
            elif name == 'trace':
                self.set('path')
            elif name == 'path':
                self.set('req')

    ##  Entering a with body.  Sets self.file and self.pprint.  Sets LOG.

    def __enter__ (self):
        global LOG
        LOG = self
        if self.file is None:
            if self.filename is None:
                self.file = sys.stdout
                self._on_exit = None
            elif self.filename is StringIO:
                self.file = StringIO()
                self._on_exit = 'value'
            elif isinstance(self.filename, str):
                self.file = open(self.filename, 'a')
                self._on_exit = 'close'
            self.pprint = PPrinter(self.file)

    ##  Exiting.  Closes self.file, if it is not stdout.
    #   Sets self.file to None and self.pprint to the default pprint.
    #   Sets LOG to None.  If the filename is a StringIO, this saves
    #   the contents of the file for getvalue().

    def __exit__ (self, type, value, traceback):
        global LOG
        if self.file is not None:
            if self._on_exit == 'close':
                self.file.close()
            elif self._on_exit == 'value':
                self._value = self.file.getvalue()
            self.file = None
            self.pprint = pprint
        LOG = None

    ##  If the filename is a StringIO, returns True.

    def hasvalue (self):
        return self.filename is StringIO

    ##  Returns the contents of the log file, provided that the filename
    #   is a StringIO and the logger was invoked in a with-statement.

    def getvalue (self):
        if not self.hasvalue():
            raise Exception('Logger does not support checkpointing')
        if self.file is None:
            v = self._value
            self._value = None
        else:
            v = self.file.getvalue()
            self.file = None
        return v

    ##  Print a log message, if the condition is active.

    def __call__ (self, cond, *args):
        if self.on(cond):
            self.pprint._file.write(str(self.id))
            self.pprint._file.write(' ')
            if cond == 'traceback':
                self.pprint('[traceback]')
                traceback.print_exc(file=self.pprint)
            else:
                if cond is True: s = '****'
                else: s = str(cond)
                self.pprint('[%s]' % s, *args)
            self.pprint.flush()

    ##  Print a log message unconditionally.

    def debug (self, *args):
        self.__call__(True, *args)

    ##  Hands off to self.pprint.

    def indent (self):
        return self.pprint.indent()

    ##  Hands off to self.pprint.

    def write (self, s):
        if self.file is not None:
            self.pprint.write(s)

