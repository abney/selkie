##  \package seal.nlp.mst
#   Wrapper for MST parser.

import os, subprocess, sys
from ..data.dep import datasets


##  Run the MST parser.  It does a system call to Java.

def mst (lang, fmt='orig', outfn=None, space=None):
    dataset = datasets[lang,fmt]
    assert dataset.train and dataset.test
    if not space: space = '5'
    mstdir = '/cl/pkg/mstparser'
    classpath = '%s:%s/lib/trove.jar' % (mstdir, mstdir)
    args = ('java',
            '-classpath', classpath,
            '-Xmx%s000m' % space,
            'mstparser.DependencyParser',
            'train', 'train-file:' + dataset.train,
            'test', 'test-file:' + dataset.test,
            'eval', 'gold-file:' + dataset.test,
            'format:CONLL')
    com = ' '.join(args)
    if outfn:
        out = subprocess.getoutput(com)
        f = open(outfn, 'w')
        f.write(out)
        f.close()
    else:
        os.system(com)


##  Parses multiple files.

def batch (langs, fmt='orig', space=None):
    for lang in langs:
        mst(lang, '%s.out' % lang, space)


def _main ():
    space = None
    fmt = 'orig'
    args = CommandLine('[-m mem] lang*\n' +
                       'Mem is in GB; default value: 5')
    while args.has_option():
        key = args.option()
        if key == '-m':
            space = next(args)
        elif key == '-f':
            fmt = next(args)
        else:
            args.usage()
    if len(args) == 0: args.usage()
    batch(args, fmt, space)


if __name__ == '__main__':
    _main()
