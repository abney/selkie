##  @package seal.nlp.dp.features
#   Features used by the parser.

from ..cld.seal.io import contents

##  A list of feature functions.

class FunctionList (object):

    ##  Constructor.

    def __init__ (self, specs, nulls=False):
        for spec in specs:
            assert '=' not in spec

        ##  List of specs.
        self.specs = [spec.replace(' ', '.') for spec in specs]

        ##  List of functions, one for each spec.
        self.functions = [_compile1(spec.split()) for spec in specs]

        ##  Whether to keep null values.
        self.nulls = nulls
        
    ##  Call it on a parser configuration.
    #   Each feature function is called to get a value.
    #   If nulls is True, each boolean false value is replaced with 'null';
    #   otherwise each boolean false value is deleted.
    #   The return is a list of pairs (spec, value).

    def __call__ (self, cfg):
        values = [f(cfg) for f in self.functions]
        if self.nulls:
            values = [v or 'null' for v in values]
            return list(zip(self.specs, values))
        else:
            return [pair
                    for pair in zip(self.specs, values)
                    if pair[1]]


##  Load a file containing specs and call compile() on it.  Returns a FunctionList.

def load (fn, nulls=False):
    return compile(contents(fn), nulls)

##  Processes the text of a file to get a list of specs.  Commas and/or newlines
#   separate specs.

def specs (text):
    lines = text.replace(',', '\n').split('\n')
    specs = []
    for line in lines:
        line = line.strip()
        if line: specs.append(line)
    return specs

##  Compile a list of specs.
#   The permitted specs are built recursively from the following specs, which
#   return words:
#    - 'stack' i - the i-th element of the stack.
#    - 'input' i - the i-th element of the remaining input.
#    - 'govr' w - the governor of word w.
#    - 'lc' w - the leftmost child of word w.
#    - 'rc' w - the rightmost child of word w.
#    - 'ls' w - the left sibling of word w.
#    - 'rs' w - the right sibling of word w.
#   The following may only be used as the last call in the spec:
#    - 'form' w - the form of word spec w.
#    - 'lemma' w - the lemma of word spec w.
#    - 'cpos' w - the coarse POS of word spec w.
#    - 'fpos' w - the fine-grained POS of word spec w.
#    - 'morph' w - the morph form of word spec w.
#    - 'role' w - the role of word w.

def compile (text, nulls=False):
    return FunctionList(specs(text), nulls)

def _compile1 (words):
    op = words[0]
    if op == 'stack':
        assert len(words) == 2
        n = int(words[1])
        return lambda cfg: cfg.stack(n)
    elif op == 'input':
        assert len(words) == 2
        n = int(words[1])
        return lambda cfg: cfg.input(n)
    elif op == 'form':
        f = _compile1(words[1:])
        return lambda cfg: cfg.word(f(cfg))
    elif op == 'lemma':
        f = _compile1(words[1:])
        return lambda cfg: cfg.lemma(f(cfg))
    elif op == 'cpos':
        f = _compile1(words[1:])
        return lambda cfg: cfg.cpos(f(cfg))
    elif op == 'fpos':
        f = _compile1(words[1:])
        return lambda cfg: cfg.fpos(f(cfg))
    elif op == 'morph':
        f = _compile1(words[1:])
        return lambda cfg: cfg.morph(f(cfg))
    elif op == 'govr':
        f = _compile1(words[1:])
        return lambda cfg: cfg.govr(f(cfg))
    elif op == 'role':
        f = _compile1(words[1:])
        return lambda cfg: cfg.role(f(cfg))
    elif op == 'lc':
        f = _compile1(words[1:])
        return lambda cfg: cfg.lc(f(cfg))
    elif op == 'rc':
        f = _compile1(words[1:])
        return lambda cfg: cfg.rc(f(cfg))
    elif op == 'ls':
        f = _compile1(words[1:])
        return lambda cfg: cfg.ls(f(cfg))
    elif op == 'rs':
        f = _compile1(words[1:])
        return lambda cfg: cfg.rs(f(cfg))
    else:
        raise Exception('Unrecognized function:' + repr(op))
