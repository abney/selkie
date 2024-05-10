##  @package seal.ml.split
#   Partition a dataset according to the value of a feature.

import os
from ...cld.seal import io
from ...cld.seal.sh import need_dir
from . import Problem
from .instance import Instance, get


def _subfn (fn, v):
    return os.path.join(fn, '_' + v)


##  Trainer.

class Trainer (object):

    ##  Constructor.

    def __init__ (self, train_fnc):

        ##  The training function.
        self.train_fnc = train_fnc

        ##  The problem.
        self.problem = None

        ##  The feature to split on.
        self.split_ftr = None

        ##  Value for 'not available'.
        self.na_value = None

        ##  Cutoff that counts as not available.
        self.na_cutoff = None

        ##  Training options.
        self.train_options = None

        ##  Tables.
        self.tables = None

        ##  Totals.
        self.totals = None

        ##  Predictors.
        self.predictors = None


    ##  Create.

    def create (self, problem):
        self.problem = problem
        self.split_ftr = None
        self.na_value = 'UNK'
        self.na_cutoff = 0
        self.train_options = None

        opts = problem.options
        if opts:
            if 'feature' in opts: self.split_ftr = opts['feature']
            if 'na_value' in opts: self.na_value = opts['na_value']
            if 'na_cutoff' in opts: self.na_cutoff = opts['na_cutoff']
            if 'cpt' in opts: self.train_options = opts['cpt']

        self.tables = [None,None]
        self.totals = [0,0]
        self.predictors = None

    ##  Create a table.

    def create_table (self, which, insts):
        self.tables[which] = table = {}
        self.totals[which] = 0
        for inst in insts:
            self.totals[which] += 1
            v = inst.get(self.split_ftr)
            if not v: v = self.na_value
            if which > 0 and v not in self.tables[0]:
                v = self.na_value
            if v in table: table[v].append(inst)
            else: table[v] = [inst]
        if which == 0 and self.na_cutoff:
            items = list(table.items())
            if self.na_value not in table:
                table[self.na_value] = []
            for (v,insts) in items:
                if v != self.na_value and len(insts) < self.na_cutoff:
                    table[self.na_value].extend(insts)
                    del table[v]

    ##  Iterate over the values of the split feature.

    def split_values (self):
        return iter(self.tables[0].keys())

    ##  Save the values to file.

    def save_split_values (self):
        f = open('%s/Values' % self.problem.modelfn, 'w')
        for v in sorted(self.tables[0]):
            f.write(str(v))
            f.write('\n')
        f.close()

    ##  Save the splitting parameters.

    def save_split_parameters (self):
        f = open('%s/Params' % self.problem.modelfn, 'w')
        f.write('split_ftr\t%s\n' % str(self.split_ftr))
        f.write('na_value\t%s\n' % str(self.na_value))
        f.write('totals\t%d\t%d\n' % tuple(self.totals))
        f.close()

    ##  Run it.

    def __call__ (self, problem, output=None):
        if (not problem.modelfn) or (not problem.workfn):
            raise Exception('Require both modelfn and workfn')
        self.create(problem)
        print('Sort instances', file=output)
        self.create_table(0, self.problem.train)
        if self.problem.test is not None:
            self.create_table(1, self.problem.test)
        need_dir(self.problem.modelfn)
        need_dir(self.problem.workfn)
        self.save_split_values()
        self.save_split_parameters()
        for v in self.split_values():
            p = Problem(options=self.train_options)
            p.modelfn = _subfn(self.problem.modelfn, v)
            p.workfn = _subfn(self.problem.workfn, v)
            p.train = self.tables[0][v]
            if self.tables[1] and v in self.tables[1]:
                p.test = self.tables[1][v]
            ntrain = len(p.train)
            ntest = 0
            if p.test: ntest = len(p.test)
            print('Split:', v, 'ntrain=', ntrain, 'ntest=', ntest, file=output)
            self.train_fnc(p)


##  A learning function.

class Learner (object):

    ##  Constructor.

    def __init__ (self, sublearner):

        ##  Learner for a subset.
        self.sublearner = sublearner

    ##  Train.

    def train (self, problem, output=None):
        trainer = Trainer(self.sublearner.train)
        trainer(problem, output=output)

    ##  Load a model.

    def load_model (self, modelfn):
        return Model(self.sublearner.load_model, modelfn)

    ##  Compute accuracy.

    def accuracy (self, workfn, modelfn=None, output=None):
        if not modelfn: raise Exception('Modelfn required')
        model = self.load_model(modelfn)
        correct = 0
        ntest = 0
        table = {}
        for v in model.split_values:
            m = model.get_submodel(v)
            mfn = _subfn(modelfn, v)
            wfn = _subfn(workfn, v)
            (p,c,n) = self.sublearner.accuracy(wfn, mfn)
            table[v] = (p,c,n)
            correct += c
            ntest += n
        acc = correct/ntest
        if output is not io.null:
            print('acc:', acc, 'correct=', correct, 'ntest=', ntest, file=output)
            print(file=output)
            for v in sorted(model.split_values):
                (p,c,n) = table[v]
                print(v, 'acc=', p, 'correct=', c, 'ntest=', n, file=output)
        return (acc, correct, ntest)


##  A model.

class Model (object):

    ##  Constructor.

    def __init__ (self, load_fnc, modelfn):

        ##  Load function.
        self.load_fnc = load_fnc

        ##  The model directory.
        self.dir = modelfn
        if not self.dir: raise Exception('Empty directory')

        ##  Submodels, one for each partition.
        self.submodels = {}

        ##  The values for the partitions.
        self.split_values = self.load_split_values()

        ##  The feature that is partitioned on.
        self.split_ftr = None

        ##  The value for 'not available'.
        self.na_value = None

        self.load_split_parameters()

    ##  Load the values for the partitions.

    def load_split_values (self):
        f = open('%s/Values' % self.dir)
        return [line.rstrip('\r\n') for line in f]

    ##  Load the split parameters.

    def load_split_parameters (self):
        f = open('%s/Params' % self.dir)
        for line in f:
            fields = line.rstrip('\r\n').split('\t')
            if fields[0] == 'split_ftr':
                self.split_ftr = fields[1]
            elif fields[0] == 'na_value':
                self.na_value = fields[1]
        assert hasattr(self, 'split_ftr')
        assert hasattr(self, 'na_value')

    ##  The the model for a particular partition.

    def get_submodel (self, v):
        if v in self.submodels:
            submodel = self.submodels[v]
        else:
            prefix = '%s/_%s' % (self.dir, v)
            submodel = self.load_fnc(prefix)
            self.submodels[v] = submodel
        return submodel

    ##  Run it.

    def __call__ (self, ftrs):
        v = get(ftrs, self.split_ftr, self.na_value)
        m = self.get_submodel(v)
        return m(ftrs)
