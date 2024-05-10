
.. automodule:: selkie.pyx.table

Tables — ``selkie.pyx.table``
=============================

A **table** is a persistent collection of objects of a fixed type.
A table is associated with a file and with an object class.
For example, suppose the contents of ``foo.tab`` is::

   name Abc
   age 120

   name Def
   age 87

And suppose that the class ``Foo`` is defined::

   class Foo (object):

       def __init__ (self):
           self.name = ''
	   self.age = ''

The class must permit the following pattern::

   >>> foo = Foo()
   >>> foo.name = 'Abc'
   >>> foo.age = '120'

(Unfortunately, this is inconsistent with using ``namedtuple``.  The
motivation is that we wish to permit objects having variable numbers
of attributes specified.)

Then one may load and access the table as follows::

   >>> foos = Table(Foo, 'foo.tab')
   >>> foos[0].name
   'Abc'

One may also index a table by column name (a string) or by an arbitrary
key function::

   >>> idx = Index(foos, 'name')
   >>> foos['Def']
   <Foo at 0x123123>

If the index key does not determine a unique record, one may specify
``multi=True``, in which case the values are lists of objects.
