
import unittest
from tempfile import TemporaryDirectory
from selkie.disk import TextDisk, TabularDisk


class TestDisk (unittest.TestCase):

    def test_text (self):
        lines = ['hi there', 'this is a test']
        with TemporaryDirectory() as dirname:
            disk = TextDisk(dirname)
            disk['foo'] = lines
            out = list(disk['foo'])
        self.assertEqual(out, lines)

    def test_tabular (self):
        recs = [['hi', '10'], ['bye', '20']]
        with TemporaryDirectory() as dirname:
            disk = TabularDisk(dirname)
            disk['foo'] = recs
            out = list(disk['foo'])
        self.assertEqual(out, recs)

            
