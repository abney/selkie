##  @package seal.ml.instance
#   Machine-learning instances.

from ...cld.seal.misc import as_ascii


##  The features are a list containing (att, value) pairs, or just an att
#   standing alone, which is treated as if it were (att, True).
#   Return the value for a given att, or default_value if not found.

def get (ftrs, tgt, default_value=None):
    if ftrs:
        for ftr in ftrs:
            if isinstance(ftr, tuple) or isinstance(ftr, list):
                if tgt == ftr[0]:
                    return ftr[1]
            else:
                if tgt == ftr:
                    return True
    return default_value


##  An instance.

class Instance (object):

    ##  Constructor.

    def __init__ (self, orig=None, feature_fnc=None, ftrs=None, label=None, prov=None):

        ##  The original form.
        self.orig = orig

        ##  As a feature list.
        self.ftrs = ftrs

        if feature_fnc:
            assert ftrs is None
            self.ftrs = feature_fnc(orig)

        ##  The label.
        self.label = label

        if prov is None and orig is not None:
            ##  Provenance.
            self.prov = orig.provenance()
        else:
            self.prov = prov

    ##  Calls the get() function.

    def get (self, att, default_value=None):
        return get(self.ftrs, att, default_value)

    ##  Iterate over the features.

    def __iter__ (self):
        return iter(self.ftrs)
    
    ##  Get.

    def __getitem__ (self, att):
        return get(self.ftrs, att)

    ##  Return the provenance.

    def provenance (self):
        return self.prov

    ##  Detailed string representation.

    def __str__ (self):
        ftrs = []
        for ftr in self.ftrs:
            if isinstance(ftr, tuple) or isinstance(ftr, list):
                ftr = '%s:%s' % (as_ascii(ftr[0]), as_ascii(ftr[1]))
            else:
                ftr = as_ascii(ftr)
            ftrs.append(ftr)
        return ' '.join([as_ascii(self.label)] + ftrs)

    ##  Brief string representation.

    def __repr__ (self):
        return '<Instance %s>' % self.__str__()
