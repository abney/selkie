
Generic regular files
*********************

In addition to the File
class, the module seal.cld.db.file provides several generic
regular file types.  ("Regular file" here means non-directory.)

 * Integer: value(), set(v), incr()

 * String: value(), set(s)

 * Strings: __len__(), __iter__(), __getitem__(i), __setitem__(i,s),
   append(s), insert(i,s), delete(i).  To do: rename delete to __delitem__.

 * Table: getitem(i), append(rec), __len__(), __iter__().

 * PropDict: class variable property_names; __len__(),
   __contains__(k), __iter__(), __getitem__(k),
   __get__(k), keys(), values(), items(), __setitem__(k,v).

