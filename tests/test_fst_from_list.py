
import unittest
from selkie.fst import from_list

class TestFstFromList (unittest.TestCase):

    def test_it (self):
        words = ['this', 'the', 'these', 'toe', 'to', 'cat']
        fst = from_list(words)
        lang = sorted(o[-1] for (i, o) in fst)
        self.assertEqual(lang, ['cat', 'the', 'these', 'this', 'to', 'toe'])
