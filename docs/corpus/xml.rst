
``selkie.xml`` — XML files
==========================

The module ``selkie.xml`` provides a convenient XML parser.
The standard Python library provides XML parsing,
but the facilities it provides generally signal an error when
encountering ill-formed XML.  Unfortunately, a great deal of XML on the
web is ill-formed, and aborting is not a very graceful way of dealing
with it.  The XML parser in ``selkie.xml`` is designed to be very
robust and lightweight.

XML tags
--------

.. py:function:: iter_xml_tags(fn)

   The XML parser described in the previous section calls
   ``iter_xml_tags()`` to convert the file to a stream containing a
   mix of XML tags and character data.  The function
   ``iter_xml_tags()`` is actually the constructor for a class.
   It has no methods beyond the standard iterator methods.
   For example:
      
   >>> from selkie.data import ex
   >>> from selkie.xml import iter_xml_tags
   >>> for elt in iter_xml_tags(ex('xml1')):
   ...     print(repr(elt))
   ... 
   <Tag start html [] 0>
   '\n'
   <Tag start body [('foo', 'hi&bye'), ('bar', '16')] 7>
   '\nA "little" '
   <Tag start b [] 59>
   'example'
   <Tag end b [] 69>
   '.\n'
   <Tag end body [] 75>
   '\n'
   <Tag end html [] 83>
   '\n'
   
   The elements are either of type ``Tag`` or of type ``str``.
   
   The XML standard requires quotes around attribute values, but the tag
   scanner does not insist on them.  Entity references are expanded in
   character data as well as in attribute values.

The function ``load_xml_tags()`` converts the iterator into a list:
   
>>> from selkie.xml import load_xml_tags
>>> tags = load_xml_tags(ex('xml1'))
>>> tags[0]
<Tag start html [] 0>
>>> len(tags)
12

Tags
----

A ``Tag`` instance has the following attributes.

.. list-table::

   * - ``type``
     - One of ``"start"``, ``"end"``, or ``"empty"``.
   * - ``label``
     - The label (category) of the tag.
   * - ``ftrs``
     - A list of pairs (*att, value*).
   * - ``cpos``
     - The character position in the plain text file.
   * - ``line_number``
     - The line number in the original XML file.

For example:
   
>>> tag = tags[2]
>>> tag
<Tag start body [('foo', 'hi&bye'), ('bar', '16')] 7>
>>> tag.type
'start'
>>> tag.label
'body'
>>> tag.ftrs
[('foo', 'hi&bye'), ('bar', '16')]
>>> tag.cpos
7
>>> tag.line_number
2

Note that the features are represented as a list of pairs.  If
multiple features have the same key, all will be present.

Entities
--------

The tag iterator has a method ``decode_xml_entities()`` that converts XML
entities like "&amp;" to characters ("&").
The codes are listed in ``TagIterator.entity_table``.
For example:
   
>>> from selkie.xml import TagIterator
>>> TagIterator.entity_table['amp']
'&'

One can override ``entity_table`` in a given instance of TagIterator
to add new tags.  If TagIterator is instantiated with ``entities=False``,
entity replacement is suppressed.


XML trees
---------

.. py:function:: load_xml(fn)

   The main function.  It reads an XML file and
   converts it to a tree.  Optional keyword arguments are:

    * ``entities=False`` leaves all HTML entities as-is.

    * ``multiple=True`` causes the return value to be a list of
      trees.  By default, only one tree is returned and it is an error
      if there is more than one in the file.

   To give an example, consider the file ``xml1``:
   
   >>> from selkie.io import contents
   >>> print(contents(ex('xml1')), end='')
   <html>
   <body foo="hi&amp;bye" bar=16>
   A &quot;little&quot; <b>example</b>.
   </body>
   </html>
   
   We read it as a tree:
   
   >>> from selkie.xml import load_xml
   >>> xml1 = load_xml(ex('xml1'))
   >>> print(xml1)
   0   (html
   1      ('#CDATA' '\n')
   2      (body
   3         ('#CDATA' '\nA "little" ')
   4         (b
   5            ('#CDATA' example))
   6         ('#CDATA' '.\n'))
   7      ('#CDATA' '\n'))

Each XML node is represented by a Tree instance.  It has one
nonstandard member, namely, ``ftrs``.

 * ``node.cat`` - a string, the tag label or ``'#CDATA'``
 * ``node.word`` - a string, the contents of a CDATA node
 * ``node.ftrs`` - a list of (att, value) pairs
 * ``node.children`` - a list of Tree instances, or None

The functions from ``selkie.tree`` can be useful with XML trees.
For example, one can pick out subtrees using the function ``subtrees()``.  It
takes a second argument which is either a category or a predicate.

>>> from selkie.tree import subtrees
>>> subtrees(xml1, 'b')
[<Tree b ...>]
>>> subtrees(xml1, lambda x: x.cat == '#CDATA' and x.word != '\n')
[<Tree #CDATA '\nA "little" '>, <Tree #CDATA example>, <Tree #CDATA '.\n'>]

The function ``subtree()`` is just like ``subtrees()``, except
that it returns a tree; it signals an error if the specified tree does
not exist or is not unique.

>>> from selkie.tree import subtree
>>> body = subtree(xml1, 'body')

The function ``terminal_string()``
returns the string contents of a node.

>>> from selkie.tree import terminal_string
>>> terminal_string(body)
'\nA "little"  example .\n'

The ``subtrees()`` function will not recurse inside any node that it
returns.  For example:

>>> subtrees(xml1, lambda x: not x.word)
[<Tree html ...>]

To retrieve all nodes matching a given criterion, use the function ``nodes()`` and
list comprehension:

>>> from selkie.tree import nodes
>>> [n for n in nodes(xml1) if not n.word]
[<Tree html ...>, <Tree body ...>, <Tree b ...>]

It is worth noting that the ``iter_xml_trees()`` function handles
ill-formed XML gracefully.  For example:

>>> print(contents(ex('bad.html')), end='')
<html>
<body>
<p>
This is an example with lots
of missing end tags.
<table>
<tr><th>Name <th>Rank <th>SerialNo</tr>
<tr><td>Smith <td>Corporal <td>1234567</tr>
<tr><td>Jones <td>Private <td>7654321</tr>
<tr><td>Howard <td>Major General <td>0000001</tr>
</table>
</body>

The missing end tags are inserted automatically:

>>> bad = load_xml(ex('bad.html'))
>>> rows = subtrees(bad, 'tr')
>>> for row in rows: print(terminal_string(row))
... 
Name  Rank  SerialNo
Smith  Corporal  1234567
Jones  Private  7654321
Howard  Major General  0000001

End tags are paired with the nearest matching start tag.  If there is no
start tag with the same label, the end tag is silently ignored.

Within the region spanned by a matching tag pair, there may be
unmatched start tags.  They are dealt with in a right-to-left pass, as follows.
First, every category has a "precedence" assigned to it.
(The precedence is only meaningful for HTML categories; it is
a fixed constant for any non-HTML categories.)  If the precedence is
zero (for categories ``br`` and ``img``), the unmatched start tag
is converted to an empty tag.  Otherwise, the "span" of the
unmatched start tag is grown to
cover as much material as possible, until it reaches the end of the
region defined by the encompassing explicit tag pair, or until it
encounters a node of equal or higher precedence.  In other words, no
element created from an unmatched start tag will contain a child whose
precedence is equal to or greater than its own.

To get the value for an attribute, use the function ``getvalue()``.

>>> from selkie.xml import getvalue
>>> getvalue(body, 'foo')
'hi&bye'

Tidy
----

When there are unmatched start tags, ``iter_xml_trees()`` calls the
function ``tidy()`` to decide where the end tags should go.  It
uses a table encoding intuitive operator precedences for HTML tags.
