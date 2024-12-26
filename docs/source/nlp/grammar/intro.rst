
Introduction to grammars
========================

A grammar consists of a set of syntactic rewrite rules and a
lexicon, which consists of lexical entries.
A rewrite rule combines a list of categories with a semantic
translation, and a lexical entry combines a category, word, and
semantic translation.

Let us begin with categories. A category consists of a type and a
collection of attribute values. Each type has a signature, which
determines the permissible attributes, and also specifies an order for
them.

Attribute values may either be variables or constants, and constants
may either be single atoms or atom sets.

