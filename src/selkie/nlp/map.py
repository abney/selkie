

#--  Index  --------------------------------------------------------------------

##  A specialization of dict in which keys are associated with lists of values.

class Index (dict):

    ##  Constructor.

    def __init__ (self, *pairs):
        dict.__init__(self)
        if len(pairs) == 1 and hasattr(pairs[0], '__next__'):
            pairs = pairs[0]
        for (k,v) in pairs:
            self.add(k,v)

    ##  Add a value.

    def __setitem__ (self, key, value):
        if key in self:
            dict.__getitem__(self, key).append(value)
        else:
            dict.__setitem__(self, key, [value])

    ##  Add a value.

    def add (self, key, value):
        self.__setitem__(key, value)

    ##  Fetch a list of values.  Returns the empty list if the key is missing.

    def __getitem__ (self, key):
        if key in self:
            return dict.__getitem__(self, key)
        else:
            return []

    ##  Iterate over all values.

    def itervalues (self):
        for vlist in dict.values(self):
            for v in vlist:
                yield v

    ##  Returns a list containing all values.

    def values (self):
        return list(self.itervalues())

    ##  Returns the number of values for the given key.

    def count (self, key):
        return len(self[key])

    ##  Deletes the given value.

    def delete (self, key, value):
        values = dict.__getitem__(self, key)
        values.remove(value)
        if not values: dict.__delitem__(self, key)

    ##  String representation.

    def __str__ (self):
        lines = ['%s -> %s' % (k, str(self[k])) for k in sorted(self.keys())]
        return '\n'.join(lines)

