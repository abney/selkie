##  @package seal.nlp.dp.nivre
#   The Nivre parser.

import os
from ..cld.seal import io, sh
from ..cld.seal.misc import Timer, as_boolean
from .parser import iterinstances, instances, ClassifierOracle, Parser as DepParser
from .features import load as load_features
from .ml import sym, split, libsvm, experiment, Problem
from ..data import dep
from .eval import evaluate as dp_evaluate

##  Save a feature function.

def save_ftrfnc (ftrfn, nulls, modelfn):
    if not os.path.exists(ftrfn):
        raise Exception('Not found: %s' % ftrfn)
    sh.need_dir(modelfn)
    io.save_string(nulls, '%s/Nulls' % modelfn)
    sh.cp(ftrfn, '%s/Features' % modelfn)
    
##  Load a feature function.

def load_ftrfnc (modelfn):
    nulls = as_boolean(io.contents('%s/Nulls' % modelfn).rstrip('\r\n'))
    ftrfnc = load_features('%s/Features' % modelfn, nulls)
    return ftrfnc

##  Create an experiment.

def create (e):
    if isinstance(e, str):
        fn = '%s.exp' % e
        e = experiment.load_experiment(fn)
    for key in ['experiment', 'features', 'nulls', 'dataset', 'split']:
        if key not in e:
            raise Exception('Missing spec: %s' % key)
    dir = e['experiment']['dir']
    name = e['experiment']['name']
    modelfn = e['experiment']['model']
    workfn = e['experiment']['work']
    ftrfn = '%s/%s.ftrs' % (dir, e['features'])
    save_ftrfnc(ftrfn, e['nulls'], modelfn)
    sh.need_dir(workfn)
    io.save_nested_dict(e, '%s/Experiment' % workfn)
    return Trainer(name, workfn)


##  Training.

class Trainer (object):

    ##  Constructor.

    def __init__ (self, name, workfn):

        ##  A nested dict.
        self.specs = io.load_nested_dict('%s/Experiment' % workfn)

        ##  The model filename.
        self.modelfn = self.specs['experiment']['model']

        ##  The work filename.
        self.workfn = workfn

        ##  A FeatureList.
        self.ftrfnc = load_ftrfnc(self.modelfn)

        ##  A dataset.
        self.dataset = dep.dataset(self.specs['dataset'])

        ##  The learner.
        self.learner = split.Learner(libsvm)

        self._model = None
        self._parser = None

    ##  Loads and caches a model.

    def model (self):
        if self._model is None:
            self._model = self.learner.load_model(self.modelfn)
        return self._model

    ##  Creates and caches a parser.

    def parser (self):
        if self._parser is None:
            self._parser = Parser(self.modelfn, self.ftrfnc, self.model())
        return self._parser

    ##  Creates a Problem, constructs feature vectors, runs the learner's train() method.

    def train (self, output=None):
        timer = Timer()
        p = Problem(modelfn=self.modelfn, workfn=self.workfn)
        p.options = self.specs['split']
        p.train = iterinstances(self.dataset.sents('train'), self.ftrfnc)
        p.test = iterinstances(self.dataset.sents('test'), self.ftrfnc)
        self.learner.train(p, output=output)
        print('Elapsed time', timer, file=output)

    ##  Computes accuracy.

    def accuracy (self, output=None):
        return self.learner.accuracy(self.workfn, self.modelfn, output)

    ##  Returns a set of sentences.

    def sents (self, which):
        return self.dataset.sents(which)

    ##  Calls dp_evaluate().

    def evaluate (self, which='test', excludepunc=True, output=None):
        sents = self.sents(which)
        p = self.parser()
        return dp_evaluate(p, sents, excludepunc=excludepunc, output=output)

    ##  Prints out the details of an instance.

    def dump_instance (self, which, s, c):
        sents = self.sents(which)
        sent = sents[s]
        insts = instances(sent, self.ftrfnc)
        inst = insts[c]
        print(inst.orig)
        print()
        print(inst)


##  The parser.

class Parser (DepParser):

    ##  Constructor.

    def __init__ (self, modelfn, ftrfnc=None, model=None):

        ##  The model file.
        self.modelfn = modelfn

        ##  The feature function.
        self.ftrfnc = ftrfnc

        ##  The model.
        self.model = model

        if not ftrfnc: self.ftrfnc = load_ftrfnc(modelfn)
        learner = split.Learner(libsvm)
        if not model: self.model = learner.load_model(modelfn)
        oracle = ClassifierOracle(self.model, self.ftrfnc)
        DepParser.__init__(self, oracle)


##  Compute the accuracy, given an experiment pathname prefix.

def accuracy (prefix, output=None):
    return Trainer(prefix).accuracy(output=output)

##  Evaluate the results, given an experiment pathname prefix.

def evaluate (prefix, which='test', excludepunc=True, output=None):
    return Trainer(prefix).evaluate(which, excludepunc, output=output)

##  Train a model.

def train (prefix):
    create(prefix).train()

##  Run an experiment.

def run_experiment (e):
    dir = e['experiment']['work']
    name = e['experiment']['name']
    t = create(e)
    output = io.tee('%s/%s.out' % (dir, name))
    t.train(output)
    print(file=output)
    t.accuracy(output=output)
    print(file=output)
    t.evaluate(output=output)
    output.close()
