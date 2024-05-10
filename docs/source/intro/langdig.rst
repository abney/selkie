
Language Digitization
*********************

At first glance, Selkie is the combination of two very different
things: an "old school" natural language processing (NLP) pipeline
that is packaged as a conversational agent, and an
application for language documentation. But both are parts of a larger
research programme. (The NLP pipeline is "old school" in the sense
that it is manually written software and not a neural network.)

The aim is to support the learning of grammars as *comprehensible*
models of languages. The NLP pipeline is driven by a grammar
written in a comprehensible, and relatively lightweight,
format. And the goal of providing a language documentation tool is to
make it easier to create datasets from which grammars can be learned.

Ideally, one would like documentation for all the world's languages:
a *universal corpus*.
The computational-linguistic community has made
significant progress toward the development of such a corpus,
with the **Universal Dependencies (UD)** treebanks as the most prominent example.

The number of languages documented in the UD treebanks has been
increasing linearly since it began, almost a decade ago. But there are
two problems: (1) A UD treebank is a narrowly syntactic description;
in many cases it does not even include translations. (2) The rate of
increase in documented languages is too slow: at the current rate, it will
be almost 400 years before the UDT includes all the world's languages.

For the majority of the world's languages, it is difficult to obtain
electronic documentation. One thinks immediately of the difficulty of
obtaining audio recordings in the field, but there are reasons
to doubt that the problem is primarily one of obtaining recordings.
Bird has shown that relatively large
bodies of audio recordings can be collected in brief time periods [2880,3639,3486].
Anecdotally, two Ojibwe tribes that I have interacted with have made
audio-video recordings of immersion sessions for educational purposes,
and as a result have accumulated thousands of hours of language data
over the years.
Such observations suggest that, at least for languages that are not
yet moribund, the main difficulty is not in making primary recordings, but rather
the low throughput of the standard documentary pipeline that leads from
primary recordings to finished datasets.
The standard tools used in documentary linguistics are sophisticated
but place high demands on users; they typically emphasize finesse in
annotation over streamlining and ease of use. By contrast, the UD
approach has made progress because the annotation emphasizes 
speed and simplicity over sophistication of
annotation. A UD syntax tree is starkly simpler than a tree in a
conventional treebank.

Selkie also adopts simplicity and lightweightedness as key
design criteria.
In particular, I hope to enable speakers of the language to contribute
directly to the effort of documenting their language, and thereby
to increase the size and diversity of a universal corpus.

The question arises immediately what might motivate a language
speaker to contribute to a universal linguistic corpus.
We cannot reasonably expect speakers of
low-resource languages to be motivated by the rather esoteric aims of 
academic linguistic research.  But speaker communities—particularly
in the cases of languages in which transmission to the next
generation is faltering—often do have a
strong interest in assembling linguistic data for purposes
of language instruction and preservation.

That provides another medium-term design goal:
to support a *mutually beneficial*
collaboration between computational linguistics and speaker
communities.  The intention is to create an application that is 
not only a platform for research in machine language learning, but
also a tool to assist in human language learning. If the collaboration brings
benefit to the community, it is more likely that they will be willing
to release at least some vetted portion of the data for research use,
and even in the absence of released data, computational-linguistic
goals are served by incorporating language-learning algorithms and
their evaluation into the platform.  One may view the latter approach as bringing the
algorithms to the data rather than the data to the algorithms.
