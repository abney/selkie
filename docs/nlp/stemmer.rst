
``selkie.stemmer`` — English stemmer
====================================

Usage
-----

The module ``selkie.stemmer`` contains a morphological analyzer for English
inflectional morphology.

The main function is also called ``stemmer``:

>>> from selkie.stemmer import stemmer
>>> stemmer('dogs')
('dog', '-s')
>>> stemmer('baking')
('bake', '-ing')
>>> stemmer('this')
('this', None)

The return value is a pair of form (stem, suffix).  The
common values for *suffix* are: ``'-s'``, ``'-ed'``,
``'-ing'``, and ``None``.  In addition, there are some
irregular words whose suffix
is ``'-en'``, and the words "am" and "are" are assigned the
special suffixes ``'+1s'`` and ``'+pl'``, respectively.

Implementation
--------------

The general procedure is to strip a suffix, then apply a stem change.

There are two tables, loaded from files.  The word table maps words
to stem-suffix pairs.  The stem table maps stems to stems.

In detail, the procedure is as follows.
If the word is listed in the word table, one immediately returns the
value.  Otherwise, use the following table.

.. list-table::
   :header-rows: 1

   * - Pattern
     - Change
     - Suffix
   * - ``-ss``
     - --
     - --
   * - ``C*.s``
     - --
     - --
   * - ``-[oiS];es``
     - Reg
     - ``-s``
   * - ``-e;s``
     - --
     - ``-s``
   * - ``-eau;s``
     - -- 
     - ``-s``
   * - ``-us``
     - --
     - --
   * - ``-is``
     - --
     - --
   * - ``-;s`` 
     - --
     - --s
   * - ``[^e]d``
     - --
     - --
   * - ``C*ed`` 
     - -- 
     - --
   * - ``-eed`` 
     - -- 
     - --
   * - ``-[C/r]red``
     - --
     - --
   * - ``-;ed`` 
     - Reg
     - ``-ed``
   * - ``not(-ing)``
     - --
     - --
   * - ``-.y;ing`` 
     - Reg
     - --ing
   * - ``C*ing`` 
     - -- 
     - --
   * - ``-[C/r]ring``
     - --
     - --
   * - ``-;ing`` 
     - Reg
     - ``-ing``
   * - ``-man;``
     - ``men``
     - ``-s``


Notes:

 * Patterns match in the order given.  It will be noticed that more
   general patterns are always listed later; they would shadow more
   specific versions otherwise.

 * ``;`` marks the end of the stem in the pattern.

 * *V* is a category in context.  It matches ``[aeiou]``, but not
   *u* immediately preceded by *q*.  It also matches *y* when
   it is preceded and followed by ``[#aeiou]``, where ``#`` is
   word boundary.

 * *C* is a category in context.  It matches anything that *V* does not match.

 * *S* matches ``szxh``.

 * ``[C/r]`` represents a single character that matches *C* but
   does not match *r*.

 * The ``men`` stem change converts *-men* to *-man*.

The procedure represented by the ``Reg`` stem change is as follows.
If the stem is listed in the stem-change table, return the value given there.
Otherwise, use the rules listed in the following table.

.. list-table::
   :header-rows: 1

   * - Pattern
     - Replacement
   * - ``-;i``
     - ``y``
   * - ``-u;``
     - ``e``
   * - ``-[aeo]``
     - --
   * - ``-x;x``
     - ε
   * - ``-x;``
     - ε
   * - ``-[tz]z``
     - --
   * - ``-z;``
     - ``e``
   * - ``-ss``
     - --
   * - ``-s;``
     - ``e``
   * - ``-[ei]t``
     - --
   * - ``-v;v``
     - ε
   * - ``-g;g``
     - ε
   * - ``-c;c``
     - ε
   * - ``-[vgc];``
     - ``e``
   * - ``-f;f``
     - ε
   * - ``-[wre]l|-[ui]al|Mll``
     - --
   * - ``-l;l``
     - ε
   * - ``-Cl;``
     - ``e``
   * - ``-r;r``
     - ε
   * - ``-Cr;``
     - ``e``
   * - ``-th;``
     - ``e``
   * - ``.[yw];``
     - ``e``
   * - ``-[yw]``
     - --
   * - ``-VCC?ic;k``
     - ε
   * - ``-C;C|`` and ``-\1;\1``
     - ε
   * - ``-Cy.;``
     - ``e``
   * - ``-CC``
     - --
   * - ``-iaC;|-u[ai]C;``
     - ``e``
   * - ``-VVC``
     - --
   * - ``-[eo][mnr]``
     - --
   * - ``-;``
     - ``e``

Note:

 * The pattern *M* stands for a monosyllable: a string containing
   only one *V*.

