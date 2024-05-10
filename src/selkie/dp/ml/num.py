##  @package seal.ml.num
#   Numeric-valued features.

from ...cld.seal.io import infile, outfile, close
from . import sym
from .instance import Instance


#--  Coder  --------------------------------------------------------------------

##  Coder.

class Coder (object):

    ##  Constructor.

    def __init__ (self, instances=None, filename=None):
        if instances is None:
            if filename is None:
                ##  Labels.
                self.labels = None
                ##  Features.
                self.features = None
            else:
                self.load(filename)
        else:
            assert filename is None
            self.create(instances)

    ##  Create the coder from instances.

    def create (self, insts):
        self.labels = {}
        self.features = {}
        out = []
        for inst in insts:
            label = inst.label
            if label in self.labels:
                label_id = self.labels[label]
            else:
                label_id = len(self.labels) + 1
                self.labels[label] = label_id
            pairs = []
            for ftr in inst.ftrs:
                if ftr in self.features:
                    ftr_id = self.features[ftr]
                else:
                    ftr_id = len(self.features) + 1
                    self.features[ftr] = ftr_id
                pairs.append((ftr_id, 1))
            einst = Instance(orig=inst, label=label_id, ftrs=sorted(pairs))
            out.append(einst)
        return out

    ##  Get the ID for the given label.

    def label (self, label):
        return self.labels[label]

    ##  Suitable for decoding numeric labels.

    def label_list (self):
        out = [None] * (len(self.labels) + 1)
        for (label, i) in self.labels.items():
            out[i] = label
        return out

    ##  Get the value for the given feature.

    def feature (self, ftr):
        return self.features[ftr]

    ##  Return a list of pairs in which feature values are replaced with ints.

    def encode_features (self, ftrs):
        pairs = []
        for ftr in ftrs:
            if ftr in self.features:
                ftr_id = self.features[ftr]
                pairs.append((ftr_id, 1))
        return sorted(pairs)

    ##  Call the coder on an instance.  Returns an Instance.

    def __call__ (self, inst):
        label = inst.label
        if label is None or label not in self.labels:
            label_id = 0
        else:
            label_id = self.labels[label]
        return Instance(orig=inst, label=label_id, ftrs=self.encode_features(inst.ftrs))

    ##  Iterate over instances.

    def iter_encode (self, insts):
        for inst in insts:
            yield self(inst)

    ##  Return a list of encoded instances.

    def encode (self, insts):
        return list(self.iter_encode(insts))

    ##  Save the coder to a file.

    def save (self, fn):
        f = outfile(fn)
        f.write('Labels\n')
        for (label, id) in self.labels.items():
            if not isinstance(label, str):
                raise Exception('Label is not a string: %s' % repr(label))
            f.write(label)
            f.write('\t')
            f.write(str(id))
            f.write('\n')
        f.write('Features\n')
        for ((a,v), id) in self.features.items():
            if not isinstance(a, str):
                raise Exception('Attribute is not a string: %s' % repr(a))
            if not isinstance(v, str):
                raise Exception('Value is not a string: %s' % repr(v))
            f.write(a)
            f.write('\t')
            f.write(v)
            f.write('\t')
            f.write(str(id))
            f.write('\n')
        close(f)

    ##  Load the contents from a file.

    def load (self, fn):
        self.labels = {}
        self.features = {}
        f = infile(fn)
        assert next(f) == 'Labels\n'
        while True:
            line = next(f)
            if line == 'Features\n': break
            (label, count) = line.rstrip('\r\n').split('\t')
            count = int(count)
            self.labels[label] = count
        for line in f:
            (a, v, count) = line.split('\t')
            count = int(count)
            self.features[a,v] = count


#--  Decoder  ------------------------------------------------------------------

##  Decoder.

class Decoder (object):

    ##  Constructor.

    def __init__ (self, coder=None, filename=None):

        ##  The features.
        self.features = None

        ##  The labels.
        self.labels = None

        if coder is None:
            assert filename is not None
            self.load(filename)
        else:
            assert filename is None
            self.invert(coder)

    ##  Build it by inverting a coder.

    def invert (self, coder):
        self.labels = [None for i in range(len(coder.labels) + 1)]
        for (lab,id) in coder.labels.items():
            self.labels[id] = lab
        self.features = [None for i in range(len(coder.features) + 1)]
        for (ftr,id) in coder.features.items():
            self.features[id] = ftr

    ##  Load it from a file.

    def load (self, fn):
        lines = [line.rstrip('\r\n').split('\t') for line in infile(fn)]
        assert lines[0] == ['Labels']
        fi = lines.index(['Features'])
        nlabels = fi - 1
        nftrs = len(lines) - (fi+1)
        self.labels = [None for i in range(nlabels+1)]
        for i in range(1,fi):
            (lab,id) = lines[i]
            id = int(id)
            self.labels[id] = lab
        self.features = [None for i in range(nftrs+1)]
        for i in range(fi+1, len(lines)):
            (a,v,id) = lines[i]
            id = int(id)
            self.features[id] = (a,v)

    ##  Return the label given an ID.

    def label (self, id):
        return self.labels[id]

    ##  Return a feature given an ID.

    def feature (self, id):
        return self.features[id]

    ##  Transform an instance.

    def __call__ (self, inst):
        label = self.labels[inst.label]
        ftrs = [self.features[ftr[0]] for ftr in inst.ftrs]
        return Instance(orig=inst, label=label, ftrs=ftrs)

    ##  Iterates over multiple instances.

    def iter_decode (self, insts):
        for inst in insts:
            yield self(inst)

    ##  Returns a list of decoded instances.

    def decode (self, insts):
        return list(self.iter_decode(insts))


#--  Instances  ----------------------------------------------------------------

##  Save instances to file.

def save_instances (insts, fn, provenance_fn=None):
    f = outfile(fn)
    if provenance_fn: pf = outfile(provenance_fn)
    else: pf = None
    for inst in insts:
        f.write(str(inst.label))
        for (a,v) in inst.ftrs:
            f.write(' ')
            f.write(str(a))
            f.write(':')
            f.write(str(v))
        f.write('\n')
        if pf is not None:
            pf.write(inst.provenance() or '')
            pf.write('\n')
    close(f)
    if pf is not None: close(pf)

##  Print a set of instances.

def print_instances (insts):
    for inst in insts:
        words = [str(inst.label)]
        for (a,v) in inst.ftrs:
            words.append(str(a) + ':' + str(v))
        print(' '.join(words))

##  Iterate over the instances in a file.

def iter_instances (fn):
    f = infile(fn)
    for (lno, line) in enumerate(f):
        fields = line.rstrip('\r\n').split()
        label = int(fields[0])
        ftrs = []
        for ftr in fields[1:]:
            i = ftr.index(':')
            a = int(ftr[:i])
            v = ftr[i+1:]
            if '.' in v: v = float(v)
            else: v = int(v)
            ftrs.append((a,v))
        yield Instance(label=label, ftrs=ftrs, prov='%s:%s' % (fn, lno))

##  Returns a list of instances read from a file.

def load_instances (fn):
    return list(iter_instances(fn))
