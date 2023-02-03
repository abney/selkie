
import unittest
from selkie.data import path
from selkie.corpus import JsonCorpus


class TestCorpus (unittest.TestCase):

    def setUp (self):
        self.corpus = JsonCorpus(path('examples/corp22.lgc'))

    def test_langs (self):
        langs = self.corpus['/langs']
        self.assertEqual(langs, {'langs': [{'langid': 'deu', 'name': 'German'}]})
        
