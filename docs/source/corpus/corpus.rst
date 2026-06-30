
Python API — ``selkie.corpus``
==============================

The general class is Dict. It is specialized by providing \verb|__keys__|,
which should be a dict mapping node types to their level. In
particular, Corpus is defined:
\begin{myverb}
class Corpus(Dict):
    __keys__ = {
        'lang': 0,
        'rom': 0,
        'text': 1,
        'lexicon': 1,
        'trans': 1,
        'sent': 2,
        'form': 2,
        'xlexicon': 2,
        'xtext': 2,
        'times': 3
    }
\end{myverb}

The class Corpus can be imported directly from {\tt selkie.corpus}:
\begin{myverb}
>>> from selkie.corpus import Corpus
\end{myverb}
Open the corpus by instantiating the Corpus class:
\begin{myverb}
>>> corpus = Corpus('example.cld')
\end{myverb}
The corpus has the form of a dict in which values may be either
strings or dicts.
\begin{myverb}
>>> list(corpus)
['lang.deu']
>>> deu = corpus['lang.deu']
>>> list(deu)
['name', 'glot', 'iso3', 'text.1', 'text.2', 'text.3', 'lexicon']
>>> deu['text.1']
{'ti': 'Eine kleine Geschichte', 'ty': 'story', 'ch': '2 3'}
\end{myverb}
The corpus has {\tt read()} and {\tt write()} methods to read or write
contents from an open file, and {\tt load()} and {\tt save()} methods
that take filenames. The form that is written does not include
indentation.
