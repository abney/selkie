##  @package seal.ml.experiment
#   A machine-learning experiment.

import os
from ...cld.seal.io import load_nested_dict, split_suffix
from ...cld.seal.misc import CommandLine, load_module


##  Load from file.

def load_experiment (fn):
    fn = os.path.abspath(os.path.expanduser(fn))
    (dir, name) = os.path.split(fn)
    (name, suffix) = split_suffix(name)
    e = load_nested_dict(fn)
    if 'experiment' in e:
        d = e['experiment']
    else:
        d = {}
        e['experiment'] = d
    if 'name' not in d: d['name'] = name
    if 'dir' not in d: d['dir'] = dir
    if 'filename' not in d: d['filename'] = fn
    if 'model' not in d: d['model'] = os.path.abspath('model')
    if 'work' not in d: d['work'] = os.path.abspath('work')
    return e

##  Run it.

def run (fn):
    e = load_experiment(fn)
    if 'command' not in e:
        raise Exception("Experiment needs to set 'command': %s" % fn)
    module = load_module(e['command'])
    if 'run_experiment' not in module.__dict__:
        raise Exception("Command module does not contain 'run_experiment': %s" % e['command'])
    f = module.__dict__['run_experiment']
    f(e)


##  Executable.

def main ():
    args = CommandLine('expfn', nargs=1)
    run(args[0])


if __name__ == '__main__':
    main()
