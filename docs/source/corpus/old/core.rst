
.. automodule:: selkie.corpus.core

Corpus Implementation — ``selkie.corpus.core``
==============================================

The corpus is built on top of a VDisk that associates Files with
names.

ItemDisk
--------

The first layer on top of the VDisk is an ItemDisk, which wraps each
File in an Item and maintains a dict in which the Items are cached.
The items represent the entire essential content
of the corpus. Items are created on demand, by a call to
``intern()``, and cached. This assures that there is only
one copy of any given item.

An ItemDisk intentionally provides no way of testing for the existence
of, or enumerating, items bottom-up. A corpus keeps its own lists of
e.g. texts and languages, and a text is considered to exist if it
exists in the list, whether or not there is a corresponding text item
on disk.

The ItemDisk provides functionality to buffer modified items
and save them all at once. By buffering, one has the
convenience of making multiple small edits to an item without incurring
the efficiency cost of writing the file multiple times.

.. py:class:: ItemDisk

   Wraps a VDisk and adds the ``hold()`` and ``modified()`` methods.
   Call ``hold()`` in a 'with' clause to hold saves until the 'with'
   clause is ended.

   .. py:method:: filename()

      Returns the pathname of the VDisk's directory.

   .. py:method:: corpus()

      Returns the corpus that this disk belongs to. The ItemDisk
      itself makes no use of this information; it merely relays it to
      Items that are created on this disk.

   .. py:method:: hold()

      This should be called in a "with" clause::

         with disk.hold():
             (edit items of disk)

      When the "with" clause exists, the "hold" object notifies the
      disk. The disk keeps a count of active holds, and when the last
      one exits, the disk saves all modified items.

   .. py:method:: intern(name, [class, *args])

      Fetch the item with the given name, creating it if necessary.
      Names are path-like. They always begin with slash, and may
      contain internal slashes.

      If this is the first time that the item is interned, *class*
      must be provided and must be a class that specializes
      Item. *Args* represents any extra
      arguments that its constructor requires (other than the disk and
      item name).

   .. py:method:: __delitem__(name)

      Delete the item with the given name. It signals an error if the
      name has never been interned.

   .. py:method:: rmtree(pfx)

      Deletes every item whose item name begins with *pfx*.


Items
-----

The Files are wrapped in Items. The class of the item determines the
Format to use to open the file. The contents of the file are stored in
the item, and the item manages edits. When writing a subclass of Item,
each method that changes the item's contents should call
``modified()`` to notify the ItemDisk that the item has been
modified. The disk tells the Item to save the contents to the file
when all holds have been released, or immediately, if there are no
current holds.

Each specialization of Item has a ``format`` member that is
used as the File class for that item. That is, the item class
determines the file format.

Nothing is cached in the item except the contents that are read from the
file (and written to it, when modifications are made).
The only exception is the creation of backlinks. If the Item
specialization has a value for ``backlinks_class``, the
``backlinks()`` method instantiates that class and caches the instance,
the first time it is called. When the ``modified()`` method of an item
that has backlinks is called, the cached value for backlinks is
cleared, forcing the backlinks to be regenerated they next time they
are needed.

.. py:class:: Item(disk, name)

   The item uses the *disk* and *name* to get the (unformatted) File
   that contains its contents. The ``format`` is then applied, and the
   result is cached. However, the file is not read until
   ``contents()`` is called for the first time.

   Items are hashable and comparable, so that they can be used in
   sets. For the purpose of hashing or comparison, an Item is
   equivalent to its name. (We here assume that items are managed by
   an ItemDisk, assuring that there is a unique item associated with
   any name.)

   .. py:attribute:: debug
   
      This is a class attribute. If one sets it to True, debugging
      information is printed out as items are read from and written to
      disk::
   
         Item.debug = True
   
   .. py:attribute:: format
   
      A specialization of Item must set the value for this class
      attribute.
   
   .. py:attribute:: backlinks_class
   
      This is also a class attribute. It may be set by specializations
      to indicate what class to instantiate to create a backlinks
      object. If it is not provided, a call to ``backlinks()`` will
      signal an error.
   
   .. py:method:: disk()

      Returns the ItemDisk.

   .. py:method:: corpus()

      Returns the corpus (which is obtained from the disk).

   .. py:method:: item_name()

      Returns the name of the item. It begins with a slash and may
      contain interior slashes.

   .. py:method:: filename()

      Returns the physical filename of the item file. For debugging.

   .. py:method:: contents()

      The first time this is called, the file is read and
      the output is cached. The return value is the cached contents.
    
   .. py:method:: backlinks()

      The first time this is called, the ``backlinks_class`` is called
      to create a backlinks object, which is cached. The return value
      is the cached backlinks object.
        
   .. py:method:: modified()

      If the contents are modified, one must call this method to
      notify the disk.

   .. py:method:: modifying()

      This can be called in a "with" clause to execute a hold on the
      disk, so that one can do multiple edits to this item with just
      one file write.

Corpus
------

.. py:class:: Corpus(root)

   *Root* is a pathname. It may begin with '~'.

   A Corpus wraps an ItemDisk. The corpus *root* is the directory that
   corresponds to the root of the item-name "filesystem".

   .. py:method:: disk()

      Returns the ItemDisk.


   .. py:method:: filename()

      Returns the root filename.

   .. py:method:: list_files()

      For debugging. Prints out all pathnames of existing regular
      files under the root pathname. If there are no stray files, each
      of these is the item name of an existing item.

   .. py:method:: item(name)

      Returns the item with the given *name*, if it exists. Signals an
      error otherwise.

   .. py:method:: intern(name[, cls, *args])

      Dispatches to the ItemDisk, which
      returns the item with the given *name*. If it does not already
      exist, it instantiates it by calling *cls* on *args*, and adds
      it to the table of items.
        
   .. py:attribute:: langs

      This attribute is a synonym for the item "/langs", which is a
      LanguageTable. It is a lazy attribute: the LanguageTable is
      created the first time it is accessed.

   .. py:attribute:: roms

      The value is a RomTable. It is not interned in the item table,
      since it is a subdirectory, not an item. The value is not
      cached - accessing ``roms`` twice returns two different objects,
      but they behave identically.

   .. py:method:: __getitem__(name)

      The same as ``.langs[name]``.

   .. py:method:: get(name)

      The same as ``.langs.get(name)``.

   .. py:method:: __iter__()

      Iterates over the language IDs.

   .. py:method:: languages()

      Iterates over the language IDs.

   .. py:method:: __len__ (self):

      Returns the number of languages.

   .. py:method:: language(name)

      Same as ``.get(name)``.

   .. py:method:: new(langid, fullname)

      Same as .langs.new(langid, fullname).

   .. py:method:: __delitem__(langid)

      Deletes the language.

      .. caution::

         This deletes all items belonging to the language and cannot
	 be undone.

Language Table
--------------

The only thing a Corpus directly contains is a LanguageTable,
accessible as ``corpus.langs``.

.. py:class:: LanguageTable

   This is an Item, and resides in the file "langs" at the top level
   of the corpus directory. Conceptually, the contents consist of a
   dict mapping language IDs to objects, where an object is a dict
   mapping attributes to values. When one fetches an object, it is
   wrapped in a Language instance. Each call returns a different
   instance, but two Language instances with the same ID will behave
   identically.

   .. py:method:: __getitem__(langid)

      Returns the language with the given ID. Signals an error if
      there is no such language in the table.

   .. py:method:: get(langid)

      Returns the language with the given ID. Returns None if there is
      no such language in the table.

   .. py:method:: __iter__()

      Iterates over the language IDs.

   .. py:method:: __len__()

      Returns the number of languages in the table.

   .. py:method:: items()

      Iterates over (*langid*, *lang*) pairs.

   .. py:method:: keys()

      Iterates over language IDs.

   .. py:method:: values()

      Iterates over Language objects.

   .. py:method:: __bool__()

      Returns False if the table is empty, True otherwise.

   .. py:method:: __delitem__(langid)

      Deletes the language from the table, and also **deletes the entire
      language subdirectory on disk.** Use with caution.

   .. py:method:: new(langid, fullname)

      Creates a new language with the given ID and (human-readable) name.
      Signals an error if a language with the given ID already exists.
      Returns the Language object.

   .. py:method:: __str__()

      A string suitable for printing, containing the IDs and names of
      languages in the table.

Language
--------

A Language is not an item. It corresponds to one entry in the
LanguageTable, and also to a subdirectory on disk. (The entire
LanguageTable is a single item.) Accordingly, Language instances are
not cached, and do not contain cached information. Multiple instances
that share the same language ID behave identically.

.. py:class:: Language(table, entry)

   The Language class is instantiated by several methods of
   LanguageTable. *Table* is the LanguageTable and *entry* is the
   entry for this language. The entry associates language properties
   ("id", "name") with values.

   .. py:method:: corpus()

      Returns the corpus that the LanguageTable belongs to.

   .. py:method:: disk()

      Returns the ItemDisk associated with the corpus.

   .. py:method:: __getitem__(prop)

      Returns the value for the given language attribute. Valid
      attribute names are: ``id``, ``name``.

   .. py:method:: __iter__()

      Iterates over the properties of the language.

   .. py:method:: __len__()

      Returns the number of properties.

   .. py:method:: __setitem__(prop, value)

      Sets the value of the property. However, the value of "id" is
      not mutable; an error is signalled if one attempts to set it.

   .. py:attribute:: lexicon

      Fetches the lexicon (which is an item).

   .. py:attribute:: index

      Fetches the token index (which is an item).

   .. py:attribute:: toc

      Fetches the table of contents (which is an item).

   .. py:attribute:: txt

      Creates a new instance of TextTable each time it is
      accessed. They all behave identically.

   .. py:method:: langid()

      Same as ``self[langid]``.

   .. py:method:: fullname()

      Same as ``self.get('name', '(no name given)')``

   .. py:method:: item_name()

      Returns the language ID, prefixed with a leading slash.

   .. py:method:: print_tree()

      Prints out the hierarchical structure of the texts.

   .. py:method:: get_roots()

      Returns the list of root texts.

   .. py:method:: get_collections()

      Returns the list of texts whose type is 'collection'.

   .. py:method:: get_documents()

      Returns the list of documents. A document is defined to be a
      maximal text that is not a collection. That is, it is not a
      collection, and it either has no parent or its parent is a
      collection.

   .. py:method:: get_vocabularies()

      Returns the list of texts whose type is "vocab".

   .. py:method:: get_simple_texts()

      Returns the list of simple texts.
      A simple text is one that is not a collection and has no children.

   .. py:method:: get_running_texts()

      Returns the list of simple texts that are not vocabularies.

   .. py:method:: words()

      Returns the list of words that results from concatenating all
      simple texts. The return value is a selkie.pyx.LazyList, which
      wraps an iterator and only fetches elements as
      required. Caution: if you modify any texts after calling
      ``words()``, the behavior of the list is unpredictable.

   .. py:method:: sents()

      Returns the list of sentences that results from concatenating
      all simple texts. The return value is a LazyList.

   .. py:method:: deref(loc)
   
      Returns the sentence at the given location. If the location 
      includes a third component, it returns a token rather than a
      sentence. If *loc* is not an instance of Loc, but rather an
      iterable containing Locs, the return value is an iteration over
      sentences or tokens.

   .. py:method:: clear_index()

      Clears the token index.

   .. py:method:: __str__()

      Dispatches to the TOC.


Toc and TextTable
-----------------

Both the Toc and TextTable are tables that contain texts. The
difference between them is that the values in the Toc are TextMetadata
instances, whereas the values in a TextTable are Text instances.

.. py:class:: Toc(disk, name, lang)

   A Toc is an Item. Its contents map text IDs to metadata entries.

   .. py:method:: language()

      The language that this Toc belongs to.

   .. py:method:: langid()

      The language ID of the language that this Toc belongs to.

   .. py:method:: text_table()

      The corresponding TextTable.

   .. py:method:: __getitem__(textid)

      Fetches the metadata entry and wraps it in a TextMetadata
      instance. It generates a new instance each time it is called,
      but all instances that share the same text ID behave
      identically.

   .. py:method:: get(textid)

      Like ``__getitem__()``, but returns None if the text does not
      exist.

   .. py:method:: __iter__()

      Iterates over the text IDs.

   .. py:method:: __len__()

      Returns the number of texts.

   .. py:method:: __bool__()

      Returns False if the Toc is empty, and True otherwise.

   .. py:method:: items()

      Iterates over (*textid*, *meta*) pairs, where *meta* is an
      instance of TextMetadata.
    
   .. py:method:: keys()

      Iterates over the text IDs.

   .. py:method:: values()

      Iterates over TextMetadata instances.

   .. py:method:: intern(textid, **kwargs)

      Returns the metadata for the text with the given ID, or creates
      a new one. The *kwargs* are only used if a new metadata entry is
      created.

   .. py:method:: new(textid, **kwargs)

      Creates a new metadata entry, and returns a corresponding
      TextMetadata instance. Signals an error if a text already exists
      with the given ID.

   .. py:method:: __delitem__(textid)

      Deletes the given text. Also deletes it from the TextTable.

   .. py:method:: __str__()

      Returns a string suitable for printing, listing text IDs, types,
      and titles.

.. py:class:: TextTable(toc, lang)

   The Toc contains the official list of text IDs. The TextTable is
   subordinate to it.

   .. py:method:: toc()

      Returns the corresponding Toc.
    
   .. py:method:: language()

      Returns the language.

   .. py:method:: langid()

      Returns the language ID.

   .. py:method:: corpus()

      Returns the corpus.

   .. py:method:: item_name()

      Technically, a TextTable is not an item, but this is the
      item-name prefix corresponding to the "txt" directory on disk.

   .. py:method:: __getitem__(textid)

      Returns a Text. Signals an error if it does not exist.
      Texts are not items, so each call returns a new instance. But Texts
      that share an ID behave identically.

   .. py:method:: __iter__()

      Iterates over text IDs.

   .. py:method:: __len__()

      Returns the number of texts.

   .. py:method:: keys()

      Iterates over the text IDs.

   .. py:method:: items()

      Iterates over (*textid*, *text*) pairs.

   .. py:method:: values()

      Iterates over Text instances.

   .. py:method:: new(textid, **kwargs)

      Creates and returns a new Text. Dispatches to Toc.intern to
      create the metadata entry. Signals an error if a text with
      the given ID already exists.

   .. py:method:: intern(textid, **kwargs)

      Either returns an existing text, or calls ``new()`` to create a
      new one.      

   .. py:method:: __delitem__(textid)

      Dispatches to the Toc.

TextMetadata and Text
---------------------

.. py:class:: TextMetadata(toc, entry)
    
   An entry in a Toc. The Toc is an item, but TextMetadata is not.

   .. py:method:: language()

      Returns the language.

   .. py:method:: corpus()

      Returns the corpus.

   .. py:method:: textid()

      Returns the value for the property "id".

   .. py:method:: text()

      Returns the corresponding Text.

   .. py:method:: __getitem__(prop)

      Returns the value for the given property. Signals an error if it
      does not exist.

   .. py:method:: get(prop[, default])

      Returns the value for the given property, or None.

   .. py:method:: __iter__()

      Iterates over the properties.

   .. py:method:: __len__()

      Returns the number of properties.

   .. py:method:: __setitem__(prop, value)

      Sets the value for the property and marks the Toc as modified.

   .. py:method:: __delitem__(prop)

      Deletes the value for the given property. Signals an error if
      one attempts to delete the value for "id".

   .. py:method:: __str__()

      Returns a string for printing, consisting of a table of
      properties and values.

.. py:class:: Text(lang, metadata)

   A Text is not an item. Its metadata is one entry in a Toc (which is
   an item), and if it is a simple text, its sentence list is an Item.

   A Text may be treated like a list. If it is a simple text, it
   behaves like a list of sentences, and otherwise, it behaves like a
   list of child Texts.

   .. py:method:: corpus()

      Returns the corpus.

   .. py:method:: language()

      Returns the language.

   .. py:method:: langid()

      Returns the language ID.

   .. py:method:: toc()

      Returns the Toc.

   .. py:method:: text_table()

      Returns the TextTable.

   .. py:method:: metadata()

      Returns the metadata, which is an instance of TextMetadata.

   .. py:method:: parent()

      Returns the parent (a Text), if it exists, and None otherwise.
      The parent relation is computed, when needed, by the Toc backlinks
      object.

   .. py:method:: has_children()

      Returns True if the text has a "ch" property (even if the value
      is empty!), and False otherwise.

   .. py:method:: children()

      Returns the list of children (of type Text) for this text.
      Returns the empty list if the text has no children.

   .. py:method:: walk()

      Iterates over the descendants of this text. The iteration starts
      with this text itself, and then recurses along children links.

   .. py:method:: pprint_tree()

      Prints ID, type, and title for all descendants of this tree,
      with indentation representing hierarchical structure.

   .. py:method:: textid()

      Returns this text's ID.

   .. py:method:: item_name()

      This is actually the name of the sentence list item (regardless
      of whether this text is actually a simple text or not).

   .. py:method:: text_type()

      Returns the value of the "ty" property, or the empty string.

   .. py:method:: title()

      Returns the value of the "ti" property, or the empty string.

   .. py:method:: author()

      Returns the value of the "au" property, or the empty string.

   .. py:method:: is_root()

      Returns True just in case this text has no parent.

   .. py:method:: is_collection()

      Returns True just in case this text's value for "ty" is "collection".
      (Note: there is no requirement that a collection have children.)

   .. py:method:: is_document_part()

      Returns True just in case this text is not a collection.

   .. py:method:: is_document()

      Returns True just in case this text is a document part, and its
      parent is not. (That is, it either has no parent, or its parent
      is a collection.)

   .. py:method:: is_simple_text()

      Returns True just in case this text is not a collection, and has
      no children.

   .. py:method:: is_vocabulary()

      Returns True just in case this text's value for "ty" is "vocab".

   .. py:method:: is_running_text()

      Returns True just in case this text is a simple text but not a vocabulary.

   .. py:method:: get_simple_texts()

      Does a walk over this text's descendants, yielding just the
      simple texts.

   .. py:method:: __iter__()

      Iterates over the elements of the text (sentences, for a simple
      text, and children, otherwise).

   .. py:method:: __getitem__(i)

      Returns the *i*-th element.

   .. py:method:: __len__()

      Returns the number of elements.

   .. py:method:: append(*args, **kwargs)

      Dispatches to the SentenceList (if this is a simple text) or
      appends a child (otherwise). The child may be represented either
      as a Text or a text ID.

   .. py:method:: sentences()

      Returns the SentenceList for this text. Only for simple texts.

   .. py:method:: tokens()

      Concatenates the tokens of all sentences in the text. Only for
      simple texts.

SentenceList, Sentence, Token, Loc
----------------------------------

The only Item that corresponds to a single text is a SentenceList,
which represents the contents of a simple text. It behaves like a list
of Sentences, and a Sentence behaves like a list of Tokens.

.. py:class:: SentenceList(disk, name, text)
    
   *Disk* and *name* are the usual Item init parameters, and *text*
   provides a back pointer to the text whose contents this
   represents.

   .. py:method:: text()

      Returns the Text.

   .. py:method:: language()

      Returns the language.

   .. py:method:: __iter__()

      Iterates over the Sentences.
            
   .. py:method:: __getitem__(i)

      Returns the the *i*-th Sentence. Note that *i* is a list index
      (0-based), not a sentence number. Each call creates a new
      Sentence instance, but all instances that share the same text and
      sentence number behave identically.

   .. py:method:: __len__()

      Returns the number of sentences.

   .. py:method:: append(sent[, gloss])

      The *sent* must be a string or an iterable containing strings and
      floats. If *gloss* is provided, it must be a string. A new
      sentence is added to the list. *Sent* and *gloss* represent its contents,
      with floats (if any) representing timestamps.
        
   .. py:method:: modified()

      When SentenceList is modified, the language's token index is
      cleared, so that it will be rebuilt the next time it is needed.

.. py:class:: Sentence(lst, sno, obj[, gloss])

   Whenever needed, a SentenceList creates a Sentence to wrap the
   internal *obj* representation. The sentence number *sno* is one
   greater than the Sentence's index in the SentenceList *lst*.

   .. py:method:: text()

      Returns the Text.

   .. py:method:: language()
		  
      Returns the language.

   .. py:method:: sno()

      Returns the sentence number (1-based).

   .. py:method:: words()

      Returns the list of tokens.

   .. py:method:: timestamps()

      Returns a list of (*i*, *time*) pairs, where *i* is a token
      index and *time* is a timestamp.

   .. py:method:: gloss()

      Returns the sentence gloss, if any.

   .. py:method:: spans([allwords])

      The timestamps determine spans, where a span has a start time,
      an end time, and a list of words as contents. If the sentence
      does not start and end with timestamps, the first and last words
      may be missing from the spans. Specifying ``allwords=True``
      causes spans to be included for all words, using None in place
      of missing timestamps. (To be precise, the first span may have
      None as start time, and the last span may have None as end time.)

   .. py:method:: __str__()

      The string representation is the concatenation of the words,
      with space separators.

.. py:class:: Token

   The words in a Sentence are of class Token. 

   Token is a subclass of str, and for that reason it is not
   possible to override the constructor. Instead, the constructor is
   invoked as ``Token_(form, sent, lexicon, loc)``.

   In addition to the methods listed here, a Token has all the methods
   of a Lexent. (They dispatch to the Lexent of the Token.) Those
   methods are: ``form()``, ``formtype()``, ``cat()``, ``gloss()``,
   ``canonical()``, ``orthographic()``, ``parts()``, ``set()``, ``partof()``,
   ``variants()``, ``locations()``, ``sentences()``, ``table()``.

   .. py:method:: sentence()

      Returns the Sentence in which this token occurs.

   .. py:method:: sentence_index()

      Returns the index (0-based) at which this token appears in the
      sentence.

   .. py:method:: lexicon()

      Returns the lexicon.

   .. py:method:: loc()

      Returns the location of this word. The value is an instance of Loc.

   .. py:method:: entry()

      Returns the lexical entry for this word.

.. py:class:: Loc(t, s[, w])

   *T* is a text ID, *s* is a sentence number (1-based), and *w* (if present) is
   a word index (0-based).

   The Loc class is hashable and comparable, so that one may use
   Locs in a set. For hashing and comparison purposes, a Loc is
   considered to be equivalent to the tuple (*t*, *s*, *w*).

   .. py:method:: from_string(s)

      A static method; creates a Loc from a string representation
      consisting of text ID, sentence number, and (optionally) word
      index, separated by periods.

   .. py:method:: t()

      Returns the text ID.

   .. py:method:: s()

      Returns the sentence number.

   .. py:method:: w()

      Returns the word index, or None.

   .. py:method:: __iter__()

      This is provided so that one can do::

         (t, s, w) = loc

   .. py:method:: __str__()

      Returns the string form, consisting of text ID, sentence number,
      and (if present) word index, separated by periods.

Lexent, Lexicon, TokenIndex
---------------------------

.. py:class:: Lexent

   A Lexent is not an item, but an entry within the Lexicon item.

   Since Lexent specializes str, it is not possible to override the
   constructor. Thie function ``Lexent_()`` is provided instead, but
   it is intended specifically for the use of Lexicon. It takes
   parameters *lexicon* and *obj*, where *obj* is a mapping from
   properties to values.

   .. py:method:: form()

      Returns the Lexent itself.

   .. py:method:: formtype()

      Returns the value for the "ty" property.

   .. py:method:: cat()

      Returns the value for the "c" property.

   .. py:method:: gloss()

      Returns the value for the "g" property.

   .. py:method:: canonical()

      Returns the value for the "cf" property.

   .. py:method:: orthographic()

      Returns the value for the "of" property.

   .. py:method:: parts()

      Processes the value of the "pp" property. Splits it at
      whitespace and interns each of the words in the lexicon.
      It is possible for the lexicon to be modified (and written) as a
      result. The return value is a list of Lexents.

   .. py:method:: set([prop=val*])

      The properties are represented using the method names above:
      ``formtype``, ``cat``, ``parts``, ``gloss``, ``canonical``,
      ``orthographic``. The value for ``parts`` should be a list of
      lexents (or tokens). The values for all the others are strings
      (which may be lexents or tokens).

   .. py:method:: partof()

      Accesses the backlink for parts. The return value is a list of
      Lexents.

   .. py:method:: variants()

      Accesses the backlink for canonical. The return value is a list
      of Lexents.

   .. py:method:: locations()

      Looks this form up in the token index. The return value is a set of locations.
      (It is guaranteed to be a newly-created set, so one may feel
      free to destructively modify it if desired.)
      If this form is not present in the token index, the iteration is empty.

      By default, the locations of forms of which this form is a part
      are also included. To suppress them, specify ``recurse=False``.

   .. py:method:: tokens()

      Iterates over the tokens of this form. It uses
      ``locations()`` to get the locations,
      and ``Language.deref_locs()`` to get the tokens at those
      locations.

      One may specify ``recurse=False``, which is passed to ``locations()``.

   .. py:method:: sentences()

      Calls ``tokens()`` and then collects the sentences for the given
      tokens. The return value is a set (to eliminate duplicates that
      might arise if there are multiple tokens in the same sentence).

      One may specify ``recurse=False,`` which is passed to ``tokens()``.

   .. py:method:: table()

      Produces a string for printing that lists all properties and
      values in tabular format.

.. py:class:: Lexicon(corpus, name, lang)

   .. py:method:: language()

      Returns the language.

   .. py:method:: corpus()

      Returns the corpus.

   .. py:method:: __iter__()

      Iterates over the entries (Lexents) of this lexicon.

   .. py:method:: __len__()

      Returns the number of entries.

   .. py:method:: __getitem__(form)

      Creates a new Lexent to wrap the raw entry of the given
      *form*. Signals an error if there is no entry.

   .. py:method:: intern(form)

      Returns a Lexent that wraps the raw entry for the given
      *form*. Creates a new entry if none exists.


.. py:class:: TokenDicts(corpus, name, lang)

   The user should not need to access this directly. It is used by the
   Lexent method ``locations()``.

   The index stores a mapping from forms to lists of locations. There
   is a reason that we store locations and not actual Tokens: to get
   the Tokens, we would need to read every text of the language in
   order to load the TokenIndex.

   .. py:method:: clear()

      Clears the table. This is called automatically whenever a simple
      text is modified.

      The index is not rebuilt until an attempt is made to access an
      index entry. In that way, we do not need to worry about multiple
      modifications to texts causing the index to be repeatedly
      rebuilt.

   .. py:method:: __getitem__(form)

      Returns the entry for the *form*, which is a set of
      Locs. Signals an error if *form* has no entry.

   .. py:method:: get(form)

      Returns the set of Locs for the given *form*. Returns an empty
      set if *form* has no entry.
