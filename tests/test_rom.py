
from unittest import TestCase
from io import StringIO
from os.path import join
from selkie import data
from selkie.corpus.rom import decode, Romanization

lords_prayer = \
'''Atta unsar thu in himinam, weihna'i namo: thein.
qima'i thiudinassus theins.  wai'rtha'i wilja theins, swe:
in himina jah ana ai'rtha'i.  hla'if unsarana thana
sinteinan gif uns himma daga.  jah afle:t uns thatei
skulans sija'ima, swaswe: jah weis afle:tam tha'im
skulam unsara'im.  jah ni briggais uns in fraistubnja'i,
ak la'usei uns af thamma ubilin; unte: theina ist
thiudangardi jah mahts jah wulthus in a'iwins.  ame:n.'''

lords_prayer_out = \
'''Atta unsar þu in himinam, weihnái namō þein.
qimái þiudinassus þeins.  waírþái wilja þeins, swē
in himina jah ana aírþái.  hláif unsarana þana
sinteinan gif uns himma daga.  jah aflēt uns þatei
skulans sijáima, swaswē jah weis aflētam þáim
skulam unsaráim.  jah ni briggais uns in fraistubnjái,
ak láusei uns af þamma ubilin; untē þeina ist
þiudangardi jah mahts jah wulþus in áiwins.  amēn.'''


class Test (TestCase):

    def test_a (self):
        self.assertEqual(decode(r'\(45)'), 'E')

    def test_b (self):
        gothic_fn = data.path('roms', 'gothic.rom')
        gothic = Romanization(fn=gothic_fn)
        with StringIO() as f:
            gothic.print_graph(f)
            s = f.getvalue()
        with open('test_rom_graph') as f:
            ref = f.read()
        self.assertEqual(s, ref)
        self.assertEqual(gothic.decode('lathi 900'), '𐌻𐌰𐌸𐌹 𐍊')

    def test_c (self):
        student_fn = data.path('roms', 'gothic-student.rom')
        student = Romanization(fn=student_fn)
        self.assertEqual(student.decode(lords_prayer), lords_prayer_out)
