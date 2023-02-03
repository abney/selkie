##  \package seal.nlp.xml
#   XML format.
#
#  One can either iterate over the tags and CDATA of the file using TagIterator,
#  or one can construct XML trees using TreeIterator.
#
#  There are convenience functions for reading from files: load_xml, load_xml_trees,
#  iter_xml_trees, load_xml_tags, iter_xml_tags.
#

import sys
from .io import Fn, infile
from .tree import Tree


#--  Iter XML tags  ------------------------------------------------------------

##  Iterate over the XML tags of a file.

def load_xml_tags (filename=None, entities=True):
    return list(iter_xml_tags(filename, entities=entities))


##  An iterator over the xml tags and CDATA blocks in a stream.  The stream
#   may be any iterator over lines.
#
#   Tags are of type Tag, and their cpos is the byte offset in the XML
#   file at which the tag begins.  Cpos values begin at 0 (not 1), and
#   they count the characters representing tags, as well as CDATA blocks.
#
#   CDATA blocks are strings.  Note that may differ from the actual characters
#   in the file, because of XML entity expansion.

class TagIterator (object):

#--  Decode XML entities  ------------------------------------------------------

##  XML entities.  Maps name to expansion.
    
    entity_table = {
        'amp'  : '&',
        'lt'   : '<',
        'gt'   : '>',
        'quot' : '"',
        'nbsp' : ' ',
        'copy' : '(c)'
        }

    ##  Constructor.

    def __init__ (self, stream, entities=True):
        if not entities:
            self.decode_xml_entities = lambda x: x

        ##  The input stream.
        self.input = stream

        ##  The lookahead buffer.
        self.lookahead = ''

        ##  The read head in the lookahead buffer.
        self.offset = 0

        ##  Where the lookahead buffer begins in the original file.
        self.cpos = 0

        ##  The current line number.
        self.line_number = 1

        ##  Whether it is in the process of a skipping something.
        self.skipping = None

        ##  Categories whose contents should not be processed.
        self.skip_categories = set(['script', 'style', 'pre'])

        ##  Skippable categories in which entities should be processed.
        self.skip_expand_entities = set(['pre'])
    
    ##  Replace all XML entities with their expansions.
    
    def decode_xml_entities (self, x):
        out = ''
        offset = 0
        while True:
            amp = x.find('&', offset)
            if amp < 0: break
            semi = x.find(';', amp+1)
            if semi < 0 or self.__any_spaces(x, amp+1, semi):
                offset = amp+1
                continue
            out += x[0:amp]
            ent = x[amp+1:semi]
            if ent in self.entity_table:
                out += self.entity_table[ent]
            else:
                sys.stderr.write('Warning: ignoring unrecognized entity &' + ent + ';\n')
            x = x[semi+1:]
            offset = 0
        out += x
        return out
    
    def __any_spaces (self, x, start, end):
        for i in range(start, end):
            if x[i].isspace(): return True
        return False
    
    ##  Returns self.

    def __iter__ (self):
        return self

    ##  Returns the i-th character in lookahead, reading more lookahead if necessary.
    #   Returns None if the i-th character is after EOF.

    def __char (self, i):
        while i >= len(self.lookahead):
            try:
                self.lookahead += next(self.input)
            except StopIteration:
                break
        if self.lookahead and i < len(self.lookahead): return self.lookahead[i]
        else: return None

    def __string (self, s, start):
        for i,c in enumerate(s):
            if self.__char(start + i) != c:
                return False
        else:
            return True

    ##  Returns the next object in the file, which is either a Tag or a string
    #   representing a CDATA block.

    def __next__ (self):
        if self.skipping:
            return self.__skip()
        c = self.__char(0)
        if not c:
            raise StopIteration
        elif c == '<':
            tag = self.__scan_tag()
            if isinstance(tag, Tag) and tag.type == 'start' and tag.label in self.skip_categories:
                self.skipping = tag.label
            return tag
        else:
            return self.__scan_cdata()

    ##  Discard the lookahead up to the current offset, which represents the end
    #   of the tag or cdata block.

    def __advance (self):
        if self.lookahead and self.offset:
            self.cpos += self.offset
            for i in range(0, self.offset):
                if self.lookahead[i] == '\n': self.line_number += 1
            self.lookahead = self.lookahead[self.offset:]
            self.offset = 0

    ##  The cdata block is terminated by '<' or EOF.

    def __scan_cdata (self):
        start = self.offset
        while True:
            c = self.__char(self.offset)
            if c is None or c == '<':
                s = self.lookahead[start:self.offset]
                self.__advance()
                return self.decode_xml_entities(s)
            else:
                self.offset += 1

    def __scan_tag (self):
        type = 'start'
        if self.__char(1) == '/':
            type = 'end'
            self.offset = 2
        elif self.__char(1) == '!':
            self.offset = 2
            return self.__scan_directive()
        elif self.__char(1) == '?':
            self.offset = 2
            return self.__scan_procinst()
        else:
            self.offset = 1

        self.__skip_whitespace()
        label = self.__scan_symbol().lower()
        ftrs = []

        ##  Scan features
        start = self.offset
        while True:
            self.__skip_whitespace()
            c = self.__char(self.offset)

            ##  premature EOF
            if c == None:
                return self.__make_tag(type, label, ftrs)

            ##  end of tag />
            elif c == '/' and self.__char(self.offset+1) == '>':
                self.offset += 2
                return self.__make_tag('empty', label, ftrs)

            ##  end of tag >
            elif c == '>' or c == '<':
                if c != '<': self.offset += 1
                return self.__make_tag(type, label, ftrs)

            ##  string value with no attribute
            elif c == '"' or c == "'":
                att = None
                value = self.__scan_quoted()

            ##  attribute and value
            else:
                att = self.__scan_symbol()
                value = None
                self.__skip_whitespace()
                if self.__char(self.offset) == '=':
                    self.offset += 1
                    self.__skip_whitespace()
                    c = self.__char(self.offset)
                    if c == '"' or c == "'": value = self.__scan_quoted()
                    else: value = self.__scan_unquoted()
                elif att:
                    value = att
                    att = None
                else:
                    att = None
                    value = self.__scan_unquoted()

            ftrs.append((att,value))
                    

    def __make_tag (self, type, label='', ftrs=None):
        cp = self.cpos
        ln = self.line_number
        self.__advance()   # this changes self.cpos and self.line_number
        return Tag(type, label, ftrs, cp, ln)

    def __skip_whitespace (self):
        while True:
            c = self.__char(self.offset)
            if c and c.isspace():
                self.offset += 1
            else:
                break

    # e.g. <pre> . . . </pre>
    # we already returned the start tag
    # now we want to return the CDATA, undigested, terminated by the end tag
    # leave the end tag to be the next thing returned

    def __skip (self):
        cat = self.skipping
        expand = cat in self.skip_expand_entities
        self.skipping = None
        terminator = '</' + cat + '>'
        n = len(terminator)
        start = self.offset
        while True:
            if self.__string(terminator, self.offset):
                s = self.lookahead[start:self.offset]
                if expand: s = self.decode_xml_entities(s)
                self.__advance()
                return s
            elif self.__char(n) is None:
                raise StopIteration
            self.offset += 1

    def __scan_symbol (self):
        start = self.offset
        while True:
            c = self.__char(self.offset)
            if not (c.isalpha() or c == ':' or c == '_' or
                    (self.offset > start and (c == '-' or c == '.' or c.isdigit()))):
                break
            else:
                self.offset += 1
        return self.lookahead[start:self.offset]

    # Note: in XML, one cannot escape quotes with backslash

    def __scan_quoted (self):
        delim = self.__char(self.offset)
        self.offset += 1
        out = ''
        start = self.offset
        while True:
            c = self.__char(self.offset)
            if c == delim or c == '\n':
                out += self.lookahead[start:self.offset]
                self.offset += 1
                return self.decode_xml_entities(out)
            else:
                self.offset += 1

    def __scan_directive (self):
        if self.__string('--', self.offset):
            self.offset += 2
            return self.__scan_xml_comment()
        elif self.__string('[CDATA[', self.offset):
            self.offset += 7
            return self.__scan_explicit_cdata()
        else:
            name = self.__scan_symbol()
            while True:
                c = self.__char(self.offset)
                if c is None or c == '>':
                    if c is not None: self.offset += 1
                    return self.__make_tag('directive', name)
                self.offset += 1

    def __scan_explicit_cdata(self):
        start = self.offset
        while True:
            if self.__char(self.offset) is None:
                s = self.lookahead[start:self.offset]
                self.__advance()
                return s
            elif self.__string(']]>', self.offset):
                s = self.lookahead[start:self.offset]
                self.offset += 3
                self.__advance()
                return s
            self.offset += 1

    def __scan_procinst (self):
        while True:
            if self.__char(self.offset) is None:
                return self.__make_tag('procinst')
            elif self.__string('?>', self.offset):
                self.offset += 2
                return self.__make_tag('procinst')
            self.offset += 1

    def __scan_xml_comment (self):
        while True:
            c = self.__char(self.offset + 2)
            if c == '>' and self.__char(self.offset) == '-' and self.__char(self.offset + 1) == '-':
                self.offset += 3
                return self.__make_tag('comment')
            self.offset += 1

    def __scan_unquoted (self):
        terminators = ' \t\n<>'
        start = self.offset
        while True:
            c = self.__char(self.offset)
            if (not c) or (c in terminators): break
            self.offset += 1
        return self.lookahead[start:self.offset]

    ##  End of processing.

    def close (self):
        self.input = None


##  Wraps TagIterator around infile(fn).

def iter_xml_tags (fn, entities=True):
    return TagIterator(infile(fn), entities=entities)


#--  Tags  ---------------------------------------------------------------------

##  An XML tag.  May be a start tag, end tag, or empty (singleton) tag.

class Tag(object):
    
    ##  Constructor.

    def __init__ (self, type, label, ftrs=None, cpos=None, line_number=None):

        ##  One of 'start', 'end', or 'empty'.
        self.type = type

        ##  The label (category) of the tag.
        self.label = label

        ##  A list of pairs (<i>att</i>, <i>value</i>).
        self.ftrs = ftrs

        ##  The character position in the plain text file.
        self.cpos = cpos

        ##  The line number in the plain text file.
        self.line_number = line_number

    ##  String representation.

    def __str__ (self):
        out = '<Tag ' + str(self.type) + ' ' + self.label + ' ' + str(self.ftrs)
        if not (self.cpos is None):
            out += ' ' + str(self.cpos)
        out += '>'
        return out

    ##  Same as str().

    def __repr__ (self):
        return self.__str__()

    ##  String suitable for printing in tabular format.

    def tabular (self):
        out = str(self.cpos) + "\t" + self.type + "\t" + self.label
        for ftr in self.ftrs:
            out += "\t"
            if ftr[0]: out += ftr[0] + "="
            if ftr[1]: out += ftr[1].replace("\t", " ").replace("\n", " ")
        return out


#--  Node  ---------------------------------------------------------------------

##  A node in an XML tree.

class Node (Tree):

    ##  Get the first child with the given category.

    def getfirst (self, cat):
        if self.children:
            for child in self.children:
                if child.cat == cat:
                    return child

    ##  Get the list of children with the given category.

    def getall (self, cat):
        if self.children:
            out = []
            for child in self.children:
                if child.cat == cat:
                    out.append(child)
            return out


#--  Load xml  -----------------------------------------------------------------

##  Load an XML file.

def load_xml (filename=None, entities=True, multiple=False):
    trees = load_xml_trees(filename, entities=entities)
    if multiple:
        return trees
    elif len(trees) == 1:
        return trees[0]
    else:
        raise Exception("File does not contain exactly one tree")

##  Load an XML file consisting (potentially) of multiple trees.

def load_xml_trees (filename=None, entities=True):
    return list(iter_xml_trees(filename, entities=entities))

##  Iterate over the trees of an XML file.

def iter_xml_trees (filename=None, entities=True):
    return TreeIterator(infile(filename), entities=entities)

##  Iterates over the XML trees in a stream.  The stream is not accessed
#   directly, but passed to TagIterator.

class TreeIterator (object):

    ##  Constructor.

    def __init__ (self, stream, entities=True):
        if not isinstance(stream, TagIterator):
            stream = TagIterator(stream, entities=entities)

        ##  The TagIterator.
        self.tags = stream

        ##  Stack of nodes being processed.  Start tag has been found but end tag not yet.
        self.stack = []

    ##  Returns self.

    def __iter__ (self): return self

    ##  The iteration method.

    def __next__ (self):
        try:
            self.scan()
        except StopIteration:
            if not self.stack:
                raise StopIteration
        if isinstance(self.stack[0], Tag):
            return self.reduce(0)
        else:
            node = self.stack[0]
            del self.stack[0]
            return node
            
    ##  Scan a subtree.

    def scan (self):
        while (not self.stack) or (isinstance(self.stack[0], Tag)):
            elt = next(self.tags)
            if isinstance(elt, str):
                if self.stack or not elt.isspace():
                    self.stack.append(Node('#CDATA', word=elt)) # a node
            elif not isinstance(elt, Tag):
                raise Exception('Not a string or tag: %s' % repr(elt))
            elif elt.type == 'start':
                self.stack.append(elt)                          # a start tag
            elif elt.type == 'end':
                start = self.find_start(elt)
                if start is not None:
                    self.stack.append(self.reduce(start))       # a node
            elif elt.type == 'empty':
                self.stack.append(tag_to_node(elt, word=''))    # a node
            elif elt.type in ('comment', 'directive', 'procinst'):
                pass
            else:
                raise Exception('Bad tag type: ' + repr(elt.type))

    ##  Find the start node for the given end tag.  Provides robustness if
    #   tags are not properly balanced.

    def find_start (self, elt):
        stack = self.stack
        for i in range(1, len(stack)+1):
            if isinstance(stack[-i], Tag) and stack[-i].label == elt.label:
                return len(stack) - i
        return None

    ##  Stack[start] must be a start tag.  Removes [start:], returns a node.

    def reduce (self, start):
        stack = self.stack
        if not isinstance(stack[start], Tag):
            raise Exception('Start elt must be a tag')
        node = tag_to_node(stack[start], tidy(stack[start+1:]))
        del stack[start:]
        return node


##  Convert a tag to a node.

def tag_to_node (tag, children=None, word=None):
    node = Node(tag.label, children=children, word=word)
    node.ftrs=tag.ftrs
    return node


#--  stream_xml  ---------------------------------------------------------------

class Streamer (object):

    def __init__ (self, stream, entities=True):
        self._tags = TagIterator(stream, entities=entities)
        self._trees = TreeIterator(self._tags)

    def tag (self):
        if self._trees.stack:
            if isinstance(self._trees.stack[0], (Tag, str)):
                tag = self._trees.stack[0]
                del self._trees.stack[0]
                return tag
            else:
                raise Exception('Next tree has already been parsed')
        else:
            return next(self._tags)
        
    def tags (self):
        while True:
            yield self.tag()

    def tree (self):
        return next(self._trees)

    def trees (self):
        return self._trees


def stream_xml (fn=None, entities=True):
    return Streamer(infile(fn), entities=entities)


#--  Getvalue  -----------------------------------------------------------------

##  Get the value for a given attribute.  Works with anything that has a 'ftrs'
#   member.

def getvalue (x, att):
    if hasattr(x, 'ftrs'):
        for ftr in x.ftrs:
            if ftr[0] == att:
                return ftr[1]
    return None


#--  Tidy  ---------------------------------------------------------------------

##  Table that maps an XML tag label to its precedence.  If a non-matching end
#   tag is found, this determines how far up the stack to search for a match.

HtmlTagTable = {
    'br'         : 0,
    'img'        : 0,
    'b'          : 1,
    'i'          : 1,
    'u'          : 1,
    'font'       : 1,
    'a'          : 1,
    'span'       : 1,
    'li'         : 2,
    'title'      : 2,
    'link'       : 2,
    'meta'       : 2,
    'area'       : 2,
    'input'      : 2,
    'map'        : 3,
    'p'          : 3,
    'ul'         : 4,
    'ol'         : 4,
    'center'     : 4,
    'blockquote' : 4,
    'form'       : 4,
    'td'         : 5,
    'th'         : 5,
    'tr'         : 6,
    'table'      : 7,
    'div'        : 8,
    'frame'      : 8,
    'body'       : 9,
    'head'       : 9,
    'frameset'   : 9,
    'html'       : 10
    }

##  Look it up in the table.

def get_precedence (label):
    if label in HtmlTagTable: return HtmlTagTable[label]
    else: return 4

##  Eliminate unmatched start tags

def tidy (items):
    i = len(items) - 1
    while i >= 0:
        if isinstance(items[i], Tag):
            if items[i].type != 'start': raise Exception('Unexpected tag type')
            cat = items[i].label
            precedence = get_precedence(cat)
            if precedence == 0:
                items[i] = tag_to_node(items[i], word='')
            else:
                end = len(items)
                for j in range(i+1, end):
                    if isinstance(items[j], Tree) \
                            and get_precedence(items[j].cat) >= precedence:
                        end = j
                        break
                node = tag_to_node(items[i], items[i+1:end])
                items[i:end] = [node]
        i -= 1
    return items
