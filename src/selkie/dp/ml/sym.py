##  @package seal.ml.sym
#   Datasets with symbolic-valued features.

import sys
from ...cld.seal.io import infile, outfile, close
from .instance import Instance


#--  Feature format  -----------------------------------------------------------

##  Iterate over the instances in a file.

def iter_instances (fn):
    f = infile(fn)
    for (lno, line) in enumerate(f):
        line = line.rstrip('\r\n')
        fields = line.split('\t')
        label = fields[0]
        ftrs = []
        for field in fields[1:]:
            i = field.find('=')
            if i < 0:
                ftrs.append(field)
            else:
                ftrs.append((field[:i], field[i+1:]))
        yield Instance(label=label, ftrs=ftrs, prov='%s:%d' % (fn, lno))

##  Load a list of instances from a file.

def load_instances (fn):
    return list(iter_instances(fn))

##  Write a symbol to a stream.

def write_symbol (s, f):
    s = str(s)
    for c in s:
        if c in '\t\n':
            raise Exception('Tab or newline in symbol')
    f.write(s)

##  Write a feature to a stream.

def write_feature (ftr, f):
    if isinstance(ftr, tuple) or isinstance(ftr, list):
        (a,v) = ftr
        assert '=' not in a
        write_symbol(a, f)
        f.write('=')
        write_symbol(v, f)
    else:
        write_symbol(ftr, f)

##  Save a set of instances to a file.

def save_instances (insts, fn):
    f = outfile(fn)
    for inst in insts:
        write_symbol(inst.label, f)
        for ftr in inst.ftrs:
            f.write('\t')
            write_feature(ftr, f)
        f.write('\n')
    close(f)

##  Print out a set of instances.

def print_instances (insts):
    f = sys.stdout
    for inst in insts:
        f.write(inst.label)
        for ftr in inst.ftrs:
            f.write(' ')
            if isinstance(ftr, tuple) or isinstance(ftr, list):
                f.write(ftr[0])
                f.write('=')
                f.write(ftr[1])
            else:
                f.write(ftr)
        f.write('\n')


#--  Feature stats  ------------------------------------------------------------

##  A table of counts.

class CountTable (dict):

    ##  Increment the value for a key.

    def incr (self, key, n=1):
        if key in self: self[key] += n
        else: self[key] = n


##  Compute statistics for a set of instances.  Returns a table of label counts
#   and a table of feature counts.

def statistics (insts):
    label_counts = CountTable()
    ftr_counts = CountTable()
    for inst in insts:
        label = inst.label
        label_counts.incr(label)
        for ftr in inst.ftrs:
            ftr_counts.incr(ftr)
    return (label_counts, ftr_counts)

##  Print out the statistics for a set of instances.

def print_stats (insts):
    (label_counts, ftr_counts) = statistics(insts)
    print('Labels:')
    items = list(label_counts.items())
    items.sort(key=lambda pair:pair[0])
    items.sort(key=lambda pair:pair[1], reverse=True)
    for (lab,ct) in items:
        print('  %6d' % ct, lab)
    print()
    print('Features:')
    items = list(ftr_counts.items())
    items.sort(key=lambda pair:pair[0])
    items.sort(key=lambda pair:pair[1], reverse=True)
    for (ftr,ct) in items:
        if (isinstance(ftr, tuple) or isinstance(ftr, list)) and len(ftr) == 2:
            print('  %6d' % ct, ftr[0], ftr[1])
        else:
            print('  %6d' % ct, ftr)
