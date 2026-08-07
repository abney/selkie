
from .lang import (
    L, sym, var, words, letters, vocab, alphabet, enum, crange, string,
    star, repeat, opt, io, invert, graph, epsilon, empty, other, rewrite,
    union, U, symbols, variables
)
from .grammar import grule
from .editor import E, F, R, done, erase, edit

# to make sure that .redist.ply exists before turning on autosym
from .redist import ply as _ply

# This causes symbols and variables to be treated as sub-modules
from . import autosym
__path__ = ['autosym::']
