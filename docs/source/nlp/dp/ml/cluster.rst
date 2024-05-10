
Clustering — ``selkie.dp.ml.cluster``
*************************************

UTM
---

The class UTM represents an upper triangular matrix.
Cells in a triangular matrix are identified by a pair of indices, but
the order of the indices does not matter.  The rows/columns of the
matrix are identified not only by index but by name.  One provides a
list of names to create the matrix::

   >>> utm = UTM(names=['foo', 'bar', 'baz'])
   >>> print(utm)
   foo bar	  0
   foo baz	  0
   bar baz	  0

Otherwise, one sets and accesses cells as one would in a regular
matrix::

   >>> utm['foo','baz'] = 10
   >>> utm['baz','bar'] = 20
   >>> utm['bar','foo'] = 6
   >>> print(utm)
   foo bar	  6
   foo baz	  10
   bar baz	  20

One may alternatively use numeric indices::

   >>> utm[1,2] = 12
   >>> print(utm)
   foo bar	  6
   foo baz	  10
   bar baz	  12
   >>> utm[2,1]
   12

The len() of the matrix is the number of rows/columns::

   >>> len(utm)
   3
