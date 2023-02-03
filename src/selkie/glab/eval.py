##  @package seal.cld.glab.eval
#   Evaluation of expressions.

import readline, traceback, io
from ..com import TimedOut
from .lang import parse_file, Funcall, Var, EvalError, Unlimited
from .functions import Environment


##  Interactive.

def console (prompt):
    try:
        while True:
            yield input(prompt)
    except EOFError:
        pass


#===============================================================================
#
#                             EVALUATOR
#

##  Get the value of __glab_function__, if any.

def as_glab_function (x):
    if hasattr(x, '__glab_function__'):
        return x.__glab_function__()


#--  Evaluation  ---------------------------------------------------------------

##  An interpreter for GLab expressions.

class Interpreter (object):

    ##  Constructor.

    def __init__ (self,
                  show_syntax=None,
                  prompt='[glab]',
                  prompt2='[parse]',
                  interruptable=False,
                  **kwargs):

        ##  The environment providing values for symbols.
        self.env = Environment(self, **kwargs)

        ##  The main prompt.
        self.prompt = prompt

        ##  The continuation prompt.
        self.prompt2 = prompt2

        ##  Conditions that are not trapped.
        self.interruptors = []
        
        if not interruptable:
            pass
        elif isinstance(interruptable, (tuple, list)):
            self.interruptors.extend(interruptable)
        else:
            self.interruptors.append(interruptable)

        if show_syntax is not None:
            self.env['*trace*'].add('syntax')
    
    ##  Evaluate an expression.  It is expected to be one of: a Funcall,
    #   a Var, or a constant.

    def eval (self, x):
        if isinstance(x, Funcall):
            return self.apply(x.function, x.args)
        elif isinstance(x, Var):
            return self.symeval(x)
        else:
            return x
    
    ##  Get the value of a symbol.

    def symeval (self, sym):
        if sym in self.env:
            return self.env[sym]
        else:
            raise EvalError('Unbound variable: %s' % str(sym))
    
    ##  Apply a function (identified by name) to arguments.

    def apply (self, fname, args):
        if isinstance(fname, str):
            if fname in self.env:
                v = self.env[fname]
                f = as_glab_function(v)
                if not f:
                    raise EvalError("Expected '%s' to name a function: got %s" % (fname, repr(v)))
            else:
                raise EvalError('Undefined function: %s' % str(fname))
        else:
            f = as_glab_function(fname)
            if not f:
                raise Exception('Not a function: %s' % repr(fname))
            fname = None
        if len(args) < f.min_nargs:
            raise SyntaxError('Too few args for %s, need %d' % (repr(f.name), f.min_nargs))
        if f.max_nargs is not Unlimited and len(args) > f.max_nargs:
            raise SyntaxError('Too many args for %s, expected %d' % (repr(f.name), f.max_nargs))
        args = list(args)
        j = 0
        for i in range(len(args)):
            if f.eval is None or f.eval[j]:
                args[i] = self.eval(args[i])
            if f.eval and j + 1 < len(f.eval):
                j += 1
        if f.types:
            j = 0
            for i in range(len(args)):
                if f.types[j] and not isinstance(args[i], f.types[j]):
                    raise EvalError("Argument %d of '%s' must be a(n) %s" % \
                        (i+1, f.name, f.types[i].__name__))
                if j + 1 < len(f.types):
                    j += 1
        if f.envarg: kwargs = {'env': self.env}
        else: kwargs = {}
        return f.implementation(*args, **kwargs)
    
    ##  Set the value of a variable.

    def set (self, vbl, value):
        self.env[vbl] = value

    ##  Evaluate a string.

    def __call__ (self, s):
        if isinstance(s, str): s = [s]
        output = io.StringIO()
        with Redirect(self.env, output):
            self._process1(s)
        s = output.getvalue()
        output.close()
        return s

    ##  Interactive version.

    def interactive (self, debugging=False):
        if debugging:
            self.env['*trace*'].add('stack')
        self._process1(console('[glab] '))

    ##  Batch version.

    def batch (self, file, debugging=False):
        if debugging:
            self.env['*trace*'].add('stack')
        if isinstance(file, str):
            with open(file) as f:
                self._process1(f, echo=True)
        else:
            self._process1(file, echo=True)

    def _process1 (self, file, echo=False):
        env = self.env
        evaluate = self.eval
        for (expr, excep, line) in parse_file(file, env):
            output = env['*output*']
            if echo: print(self.prompt, line, file=output)
            if excep:
                print('ERROR IN PARSING:', excep, file=output)
            elif expr:
                trace = env['*trace*']
                if 'syntax' in trace:
                    print(self.prompt2, expr, file=output)
                try:
                    value = evaluate(expr)
                    if value is not None:
                        print(repr(value), file=output)
                        env['_'] = value
                except Exception as e:
                    if type(e) in self.interruptors:
                        raise
                    elif 'stack' in trace:
                        traceback.print_exc(file=output)
                    else:
                        print('ERROR:', e, file=output)


##  An instance of Interpreter.
#
#       interpret = Interpreter()
#
#   That way of doing it makes it impossible to redirect output before
#   calling the interpreter.  The Interpreter captures the value of
#   stdout at the time of instantiation.  Redirecting stdout and
#   *calling* the interpreter inside of that redirection doesn't work.
#

def batch (fn, output=None):
    Interpreter(output=output).batch(fn)


##  Redirects output to a file.

class Redirect (object):

    ##  Constructor.

    def __init__ (self, env, file):

        ##  The environment.
        self.env = env

        ##  The output stream.
        self.output = file

        ##  Old value of *output*.
        self.prev_output = None

    ##  Enter.  Sets the value of '*output*' to a stream writing the file.

    def __enter__ (self):
        env = self.env
        self.prev_output = env['*output*']
        env['*output*'] = self.output

    ##  Exit.  Sets '*output*' back to its original value.

    def __exit__ (self, t, b, tb):
        env = self.env
        env['*output*'] = self.prev_output
        self.prev_output = None
