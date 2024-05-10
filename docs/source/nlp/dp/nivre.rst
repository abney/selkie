
The Nivre parser
****************

Experiment
----------

Here is an example of running an experiment::

   $ cp /cl/examples/nivre-2007.ftrs ./
   $ cp /cl/examples/nivre.exp ./
   $ python -m selkie.dp.ml.experiment nivre.exp work

This creates the directory work as a subdirectory of the current
working directory.  All output is written in work, except the
main summary, which is written to stdout and also saved in the file
nivre.out as a sister to nivre.exp.  When this particular
experiment has completed, the file nivre.out should contain,
among other things::

   ...
   acc: 0.908801020408 correct= 9975 ntest= 10976
   ...
   LAS:    3912 4991 0.783810859547
   UAS:    4102 4991 0.821879382889
   LA:     4391 4991 0.879783610499
   NSents: 206                     

The file nivre.exp is called the **experiment file**.
Omitting the .exp extension gives the **experiment name**,
which in this case is nivre.  The
directory in which the experiment file resides (the current working directory, in this
case), is called the **experiment directory**.  The directory work
is called the **working directory.**  See selkie.dp.ml.experiment.

Here is an example of an experiment file ::

   command selkie.dp.nivre
   dataset spa.orig
   features nivre-2007
   nulls True
   split.feature fpos.input.0
   split.cpt.s 0
   split.cpt.t 1
   split.cpt.d 2
   split.cpt.g 0.2
   split.cpt.c 0.5
   split.cpt.r 0
   split.cpt.e 1.0

The command is selkie.dp.nivre, which names the module.  The
function that runs the experiment is run_experiment within that
module.  The steps it goes through are the following.

 * Call save_experiment() and then
   load_experiment(), to make a persistent copy of the experiment
   and feature files in the working directory.  Loading the experiment
   also creates the feature function and loads the dataset.

 * Call the train() function to train an oracle, which is
   a classifier whose classes are parsing actions.
   The train() function converts training and testing sentences
   to instances, then uses them to train an oracle.

 * Load a Model from the working directory.

 * Call the model's accuracy() method to get the
   classification accuracy of the oracle on the test instances.

 * Call the model's evaluation() method to use the oracle to parse
   the test sentences, and determine the accuracy (LAS, UAS) of the
   resulting parser.

Output is passed through a tee so that it goes both to stdout
and to the file *expname*.out in the experiment directory.

Dataset
.......

The dataset spa.orig is Spanish, original format.  To get a list of available
datasets::

   >>> from selkie.data import dep
   >>> sorted(dep.datasets)

See selkie.data.dep.datasets for details.

Features
........

The features are nivre-2007, which are found in the file
nivre-2007.ftrs residing in the experiment directory.  Here are
the contents of the feature file ::

   form input 0
   lemma input 0
   cpos input 0
   fpos input 0
   morph input 0
   form input 1
   fpos input 1
   fpos input 2
   fpos input 3
   role lc input 0
   form stack 0
   lemma stack 0
   cpos stack 0
   fpos stack 0
   morph stack 0
   role stack 0
   fpos stack 1
   form govr stack 0
   role lc stack 0
   role rc stack 0

The first line says that the input[0].form is one feature.  The
last line says that stack[0].rc.role is one feature.
For more details, see selkie.dp.features.

Nulls
.....

There are two ways that a feature may be null: either the feature
expression (e.g., input[0].form) results in an error when
evaluated, or it results in a value that is boolean false.  If
nulls is true, then null values are represented as null.
Otherwise, features with null values are omitted from the instance.
See selkie.dp.features.

Split
.....

The parser calls selkie.dp.ml.split to do training and testing.  It
splits instances into sub-datasets and does SVM training on each
sub-dataset separately.  The value of split.feature is the
feature to use to split the dataset: each distinct value of the
feature names a separate sub-dataset.

Split.cpt
.........

The split trainer calls a learner on each sub-dataset.  Here the
learner is hardcoded as selkie.dp.ml.libsvm.  The split.cpt
settings are parameters of the libsvm learner.  See selkie.dp.ml.libsvm.

General usage
-------------

To train and use a parser, one first requires an experiment file.
Assume that ptb.exp
contains the contents::

   command selkie.dp.nivre
   dataset ptb.umap
   features delex
   nulls True
   split.feature fpos.input.0
   split.cpt.s 0
   split.cpt.t 1
   split.cpt.d 2
   split.cpt.g 0.2
   split.cpt.c 0.5
   split.cpt.r 0
   split.cpt.e 1.0

Then one creates the model directory ptb.model by doing::

   >>> from selkie.dp import nivre
   >>> nivre.train('ptb')

Training also creates the directory foo.work.  The work directory can be
used to evaluate parser accuracy, provided that the training dataset
includes a test portion as well.
There are two separate functions for measuring accuracy.  Remember
that the parser uses an oracle.  For a given test sentence, the
correct parse translates into a sequence of parsing actions, each
taken from a particular configuration.  Each configuration corresponds
to a learning instance, and the correct action is the true label.
The accuracy() function reports on the accuracy of the trained
oracle on the test instances.::

   (missing example)

It gives the
proportion of correct predictions that it makes on the testing instances.

To train:::

   >>> nivre.train('foo')

The file 'foo.exp' must exist.
This writes a lot of files, split by part of speech of INPUT[0].
The list of parts of speech occurring in training is written to
StatsTrainParts and those in test files are written to
StatsTestParts.  Training is only done where both training and
testing files exist.

To compute the accuracy of the predictions on the test files:::

   >>> nivre.accuracy()
   Accuracy: 0.581359329446 correct= 6381 ntest= 10976
   Fa acc= 0.333333333333 correct= 1 ntest= 3
   Fc acc= 0.639606396064 correct= 520 ntest= 813
   Fd acc= 0.576923076923 correct= 15 ntest= 26
   ...

Options
-------

The train() function takes the following options:

 * features: the filename of a set of feature specifications.

 * split_ftr: the attribute to use for splitting
   up the training data.
