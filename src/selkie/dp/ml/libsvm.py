##  \package seal.ml.libsvm
#   Libsvm package.

import os, sys
try:
    from libsvm import svmutil, svm_train, svm_predict
except:
    print('libsvm has not been installed', file=sys.stderr)

from ...cld.seal.misc import repeatable
from . import num, sym


#--  train  --------------------------------------------------------------------

##  Trainer.

class Trainer (object):

    ##  Constructor.

    def __init__ (self):

        ##  The learning problem.
        self.problem = None

        ##  The data coder.
        self.coder = None

        ##  Coded version of training set.
        self.train = None

        ##  Coded version of test set.
        self.test = None

    # options:
    # -s 0 = multiclass
    # -t 1 = polynomial kernel
    # -t 1 -d 2 = quadratic
    # -g gamma
    # -c cost
    # -r coef0
    # -e epsilon

    def _option_string (self):
        if self.problem.options:
            words = ['']
            for (k,v) in self.problem.options.items():
                words.append('-' + k)
                words.append(str(v))
            return ' '.join(words)
        else:
            return ''

    ##  Write instances.

    def write_instances (self, which, insts, ascinsts):
        pfx = self.problem.workfn
        fn = '%s.%s' % (pfx, which)
        provfn = '%s.%s.prov' % (pfx, which)
        ascfn = '%s.%s.asc' % (pfx, which)
        num.save_instances(insts, fn, provenance_fn=provfn)
        sym.save_instances(ascinsts, ascfn)

    ##  Save the coder.

    def write_coder (self):
        self.coder.save('%s.coder' % self.problem.modelfn)

    ##  Main call.  Sets the problem and creates a coder.

    def __call__ (self, prob):
        self.problem = prob
        self.coder = num.Coder()
        mfn = self.problem.modelfn
        wfn = self.problem.workfn

        self.problem.train = repeatable(self.problem.train)
        self.train = self.coder.create(self.problem.train)
        self.write_instances('train', self.train, self.problem.train)
        self.write_coder()
        cmd = '%s%s %s.train %s.model > %s.log' % \
            (svm_train, self._option_string(), wfn, mfn, wfn)
        os.system(cmd)

        if self.problem.test:
            self.problem.test = repeatable(self.problem.test)
            self.test = self.coder.encode(self.problem.test)
            self.write_instances('test', self.test, self.problem.test)
            os.system('%s %s.test %s.model %s.pred >> %s.log' % \
                          (svm_predict, wfn, mfn, wfn, wfn))

##  Create and call a Trainer.

def train (problem, output=None):
    Trainer()(problem)

##  Create a numeric decoder.

def decoder (modelfn):
    return num.Decoder(filename=modelfn + '.coder')

##  Decode all files.

def decode (workfn, modelfn):
    dc = decoder(modelfn)
    for suffix in ['train', 'test', 'pred']:
        fn = '%s.%s' % (workfn, suffix)
        if os.path.exists(fn):
            einsts = num.load_instances(fn)
            sym.save_instances(dc.decode(einsts), '%s.asc' % fn)

##  Load instances.

def load_instances (workfn, suffix):
    fn = '%s.%s' % (workfn, suffix)
    return num.load_instances(fn)


#--  accuracy  -----------------------------------------------------------------

##  Compute accuracy.

def accuracy (workfn, modelfn=None, output=None):
    testfn = '%s.test' % workfn
    if os.path.exists(testfn):
        truth = [inst.label for inst in num.iter_instances('%s.test' % workfn)]
        pred = [inst.label for inst in num.iter_instances('%s.pred' % workfn)]
        correct = sum(t==p for (t,p) in zip(truth, pred))
        total = len(truth)
        return (correct/total, correct, total)
    else:
        return (None, 0, 0)


#--  load_model  ---------------------------------------------------------------

##  Create a coder.

def coder (modelfn):
    coder = num.Coder()
    coder.load(modelfn + '.coder')
    return coder

##  Whether or not the model files exist.

def model_exists (model_prefix):
    model_fn = '%s.model' % model_prefix
    coder_fn = '%s.coder' % model_prefix
    return os.path.exists(model_fn) and os.path.exists(coder_fn)

##  The model.

class Model (object):

    ##  Constructor.

    def __init__ (self, prefix):

        ##  Filename prefix.
        self.prefix = prefix
        model_fn = '%s.model' % prefix

        ##  The SVM model.
        self.model = svmutil.svm_load_model(model_fn)

        ##  Coder.
        self.coder = coder(prefix)

        ##  Labels.
        self.labels = self.coder.label_list()
    
    ##  Call it.  Encode the features, call the SVM predictor, and return
    #   the predicted labels.

    def __call__ (self, ftrs):
        ftrs = dict(self.coder.encode_features(ftrs))
        (preds,_,_) = svmutil.svm_predict([0], [ftrs], self.model, '-q')
        return self.labels[int(preds[0])]


##  Load a model.

def load_model (prefix):
    return Model(prefix)
