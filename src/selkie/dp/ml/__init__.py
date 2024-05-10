##  @package seal.ml
#   Machine learning.

import os
from glob import glob
from ...cld.seal import sh, io


def _clean_prefix (pfx):
    for fn in glob(pfx + '*'):
        sh.rmrf(fn)


##  A machine-learning problem.

class Problem (object):

    ##  Constructor.

    def __init__ (self, train=None, test=None, options=None, modelfn=None, workfn=None):

        ##  Training data.
        self.train = train

        ##  Test data.
        self.test = test

        ##  Options.
        self.options = options

        ##  Model filename.
        self.modelfn = modelfn

        ##  Work filename.
        self.workfn = workfn

    ##  Create directory for model and work files, put a pointer to the work file
    #   in the model file.

    def init (self):
        sh.mkdirp(self.modelfn)
        sh.mkdirp(self.workfn)
        io.save_string(os.path.abspath(self.modelfn), '%s/ModelFN' % self.workfn)

    ##  Delete the model and work directories.

    def clean (self, which, prefix=False):
        if prefix:
            if which in ['model', 'all']:
                _clean_prefix(self.modelfn)
            if which in ['work', 'all']:
                _clean_prefix(self.workfn)
        else:
            if which in ['model', 'all']:
                sh.rmrf(self.modelfn)
            if which in ['work', 'all']:
                sh.rmrf(self.workfn)


##  Load the model file associated with a given working directory.

def load_modelfn (workfn):
    return io.contents('%s/ModelFN' % workfn).strip('\r\n')
