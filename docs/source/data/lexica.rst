
Other lexica and grammars
*************************

Census
------

The module selkie.data.census
provides an interface to a list of names from
the U.S. Census.  A sample of about 6,000,000 census entries was selected,
and the distribution of first and last names was computed.  The actual
sample of last names included only valid last-name entries, so it was
somewhat smaller than the original sample of entries.  The first-name
sample was divided by gender, so that the male sample and female
sample contain about 3,000,000 sample points each.

The basic function is get()::

   >>> from selkie.data import census
   >>> francis = census.get('Francis')
   >>> francis
   <Name FRANCIS mr=127 fr=393 lr=385>

The argument to get() is case-insensitive.  If the argument is
not found in the database, the return value is None::

   >>> francis.male.freq
   0.16
   >>> francis.female.freq
   0.039
   >>> francis.last.freq
   0.029
   >>> francis.maleness()
   0.8040201005025125

The value for francis.male or francis.female
or francis.last is a
census.Entry object, which has attributes string,
freq, cumfreq, and rank.

 * The string is the
   same as n.string, where n is the Name object::

      >>> francis.string
      'FRANCIS'

 * The freq is in percent.  It represents the percent of people in
   the sample whose name was the one given.  Note that a last name with
   frequency of 1% corresponds to an absolute count of
   about 60,000 (out of 6,000,000), whereas a first name with frequency 1%
   corresponds to an absolute count of about 30,000 (out of
   3,000,000).

 * The cumfreq is in percent::

      >>> francis.male.cumfreq
      64.25

 * The rank is an integer; the most-frequent name in the
   relevant sample has rank 1::

      >>> francis.male.rank
      127

 * The method maleness() returns the
   conditional probability that the name is male, given that it is a
   first name.  That is, if *m* is the frequency in the male entry, and
   *f* is the frequency in the female entry, maleness is *m/(m+f)*.  (If
   the name never occurs as a first name, maleness defaults to 0.5)::

      >>> jordan = census.get('jordan')
      >>> jordan.maleness()
      0.8235294117647058

A name that occurs at all has values for all three entries.  For
example, "Morrison" occurs only as a last name::

   >>> n = census.get('Morrison')
   >>> n.male.freq
   0.0
   >>> n.female.freq
   0.0
   >>> n.last.freq
   0.048

If the name occurs in none of the samples, census.get() returns
None.

One can iterate over all names by calling the function
names().

..
   Commented Out

   Internet Dictionary Project
   ---------------------------
   
   The module selkie.data.idp provides an interface to the
   Internet Dictionary Project (IDP) dictionaries.  Dictionaries are
   available for French (fra), German (deu), Italian (ita), Latin (lat),
   Portuguese (por), and Spanish (spa).  For all except Latin, the keys
   are English words and the target language translation is the value.
   For Latin, the keys are Latin words.
   
   Dictionaries are loaded on demand and cached.
   One may look up individual words as follows::
   
      >>> from selkie.data.idp import lookup # doctest: +SKIP
      >>> lookup('animal', 'deu') # doctest: +SKIP
      'Tier[Noun]'
      >>> lookup('proprius', 'lat') # doctest: +SKIP
      "one's own, permanent, special, peculiar."
   
   Alternatively, one may fetch the entire dictionary (a dict) and access
   it directly::
   
      >>> from selkie.data.idp import lexicon # doctest: +SKIP
      >>> latin = lexicon('lat') # doctest: +SKIP
      >>> latin['amor'] # doctest: +SKIP
      'love, affection, infatuation, passion.'
