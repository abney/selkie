
import unittest
from sys import argv
from os import chdir
from os.path import abspath
from selkie.glab import batch
from selkie.io import redirect, contents

notebook_dir = abspath('./glab')

def notebook_output (name):
    chdir(notebook_dir)
    with redirect():
        batch(name + '.gn')
    return redirect.output
    
def old_output (name):
    chdir(notebook_dir)
    return contents(name + '.output')


class TestGLab (unittest.TestCase):

    def run_test (self, name):
        self.assertEqual(notebook_output(name), old_output(name))

    def test_01 (self):
        self.run_test('test01')

    def test_02 (self):
        self.run_test('test02')

    def test_03 (self):
        self.run_test('test03')

    def test_04 (self):
        self.run_test('test04')

    def test_05 (self):
        self.run_test('test05')

    def test_06 (self):
        self.run_test('test06')

    def test_07 (self):
        self.run_test('test07')

    def test_08 (self):
        self.run_test('test08')

    def test_09 (self):
        self.run_test('test09')

    def test_10 (self):
        self.run_test('test10')


if __name__ == '__main__':
    usage = 'Usage: testNN [old|new]'
    if len(argv) < 2:
        print(usage)
    name = argv[1]
    if len(argv) > 2:
        com = argv[2]
    else:
        com = 'cmp'

    if com == 'cmp':
        output = notebook_output(name)
        old = old_output(name)
        if output == old:
            print('Same output')
        else:
            print('Different output')
        print('To see output: python test_glab.py', name, '(old|new)')

    elif com == 'old':
        print(old_output(name))

    elif com == 'new':
        print(notebook_output(name))

    else:
        print(usage)
