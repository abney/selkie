##  \package seal.script.doctest
#   Extracts doctest-style blocks from XML or Latex source.
#
#   Example:
#
#       $ python -m seal.script.doctest ~/git/seal/doc/html/core/misc.html
#       Extracted tests into misc.tests
#       misc.tests: 69 test(s) found, all passed
#
#   The test file is created in the current directory.
#
#   One may specify a location for the test file by adding -o <i>fn</i>.
#

import doctest
from sys import stdout
from os.path import basename, abspath, expanduser, join, exists
from seal.core.io import split_suffix
from seal.core.misc import Cwd, shift


def _unescape_html (s):
    return s.replace('&lt;', '<').replace('&amp;', '&').replace('&gt;', '>')

_usage = r'''
python -m seal.script.doctest FN

Test blocks are explicitly marked with beginning and end lines.
The form of those lines depends on the file format:

Format  Start End
------------------

html    <pre class="python">  </pre>
        <!-- python           -->

tex     \begin{python}        \end{python}
'''


_delims = {
    'html': {
        '<pre class="python">': ('', _unescape_html, '</pre>'),
        '<!--[python': ('', None, ']-->')
        },
    'tex': {
        r'\begin{python}': ('', None, r'\end{python}'),
        r'%[python': ('% ', None, '%]')
        }
    }


##  Extract test blocks from a file.
#   The source file may be anywhere.
#   If testfn is not specified, the test file is in the current working
#   directory and has the same name as the source file except that the
#   suffix is replaced with <tt>tests.</tt>  For example, if the source file
#   is <tt>/foo/bar/baz.html</tt>, the default test file is <tt>./baz.tests</tt>.
#
#   Test blocks in an html file are of two sorts:
#
#       <pre class="python">   </pre>
#       <!--[python            ]-->
#
#   Test blocks in a tex file are likewise of two sorts:
#
#       \\begin{python}        \\end{python}
#       %[python               %]
#
#   In the lattermost case, each intermediate line must begin with '% ' (percent-space).

def extract_tests (fn, testfn=None):
    fn = abspath(expanduser(fn))
    (base, suffix) = split_suffix(basename(fn))
    if not suffix:
        for s in _delims:
            if exists(base + '.' + s):
                suffix = s
                fn = base + '.' + suffix
                break
        if not suffix:
            raise Exception('Not found: %s.{%s}' % (base, ','.join(_delims)))
    delims = _delims[suffix]
    if testfn is None:
        testfn = base + '.tests'
    if testfn == '-':
        _extract_tests(fn, delims, stdout)
    else:
        with open(testfn, 'w') as outfile:
            _extract_tests(fn, delims, outfile)
    return testfn

def _extract_tests (fn, delims, outfile):
    with open(fn) as infile:
        indent = end = None
        for line in infile:
            line = line.rstrip('\r\n')
            if end is None:
                if line in delims:
                    (indent, decode, end) = delims[line]
            elif end == line:
                indent = end = None
            else:
                if indent and line.startswith(indent):
                    line = line[len(indent):]
                if not line:
                    line = '<BLANKLINE>'
                elif decode is not None:
                    line = decode(line)
                outfile.write(line)
                outfile.write('\n')

##  Run doctest on extracted blocks.

def testfile (origfn, testfn=None, extract_only=False):
    if extract_only:
        if testfn is None:
            testfn = '-'
    testfn = extract_tests(origfn, testfn)
    if testfn != '-':
        print('Extracted tests into', testfn)
    if extract_only:
        return
    flags = doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS
    with Cwd():
        (failed, tested) = doctest.testfile(testfn,
                                            module_relative=False,
                                            optionflags=flags)
    if failed == 0:
        if tested == 0: print('%s: No tests found' % testfn)
        else: print('%s: %d test(s) found, all passed' % (testfn, tested))
    else:
        raise Exception('%d test(s), %d failed' % (tested, failed))


def _scan_flags (kwargs):
    while shift.isflag():
        flag = shift()
        if flag == '-x':
            kwargs['extract_only'] = True
        elif flag == '-o':
            fn = shift()
            kwargs['testfn'] = fn
        else:
            shift.error('Unrecognized flag: %s' % flag)

##  Main function.

def main ():
    shift.set_usage(_usage)
    kwargs = {}
    _scan_flags(kwargs)
    fn = shift()
    _scan_flags(kwargs)
    testfile(fn, **kwargs)


if __name__ == '__main__':
    main()
