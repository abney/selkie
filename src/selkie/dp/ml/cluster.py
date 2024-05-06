##  @package seal.ml.cluster
#   Clustering algorithms.


#--  UTM  ----------------------------------------------------------------------

##  Upper triangular matrix.

class UTM (object):

    ##  Constructor.

    def __init__ (self, fn=None, names=None):

        ##  Contents.
        self.contents = []

        ##  Name dict.
        self.name_dict = {}

        ##  List of names.
        self.names = []

        if names:
            for name in names:
                self.__intern(name)
        if fn: self.load(fn)

    def __intern (self, name):
        if name in self.name_dict:
            return self.name_dict[name]
        else:
            idx = len(self.contents)
            self.names.append(name)
            self.name_dict[name] = idx
            self.contents.append([0 for k in range(0,idx)])
            return idx

    ##  Return the i-th name.

    def name (self, i):
        return self.names[i]

    def __digest_addr (self, addr):
        i, j = addr
        if isinstance(i, str):
            i = self.name_dict[i]
        if isinstance(j, str):
            j = self.name_dict[j]
        if j < i: (i, j) = (j, i)
        return i, j

    ##  Fetch the value at an address.

    def __getitem__ (self, addr):
        i, j = self.__digest_addr(addr)
        if i == j: return 0
        else: return self.contents[j][i]

    ##  Set the value at an address.

    def __setitem__ (self, addr, value):
        i, j = self.__digest_addr(addr)
        if i == j: raise Exception('Cannot set cell in main diagonal')
        else: self.contents[j][i] = value

    ##  Load contents from file.

    def load (self, fn):
        stream = open(fn)
        dict = {}
        for line in stream:
            line = line.strip()
            x, y, value = line.split()
            i = self.__intern(x)
            j = self.__intern(y)
            self[i,j] = float(value)

    ##  The number of entries.

    def __len__ (self):
        return len(self.contents)

    ##  Representation as file contents.

    def __str__ (self):
        return '\n'.join(
            self.name(i) + '\t' + self.name(j) + '\t' + str(self[i,j])
            for i in range(0, len(self.contents) - 1)
            for j in range(i+1, len(self.contents)))


#--  Clusterer  ----------------------------------------------------------------

##  The clustering algorithm.

class Clusterer (object):

    ##  Constructor.

    def __init__ (self, aggregator):

        ##  Upper triangular matrix.
        self.utm = None

        ##  Aggregation function.
        self.aggregator = aggregator

        ##  Active list.
        self.active_list = None

        ##  Current number of clusters.
        self.cluster_count = 0

    def __load_utm (self, utm):
        n = len(utm)
        self.active_list = [Cluster(i, utm.name(i)) for i in range(0, n)]
        for j in range(1, n):
            c = self.active_list[j]
            for i in range(0, j):
                c.set_distance(self.active_list[i], utm.get(i,j))
            c.is_active = True
        self.cluster_count = n

    def __best_pair (self):
        n = len(self.active_list)
        if n <= 1: raise Exception('Must have at least two active clusters')
        min_d = 0
        best_i = None
        best_j = None
        for j in range(1, n):
            for i in range(0, j):
                x = self.active_list[i]
                y = self.active_list[j]
                d = y.distance(x)
                if d < min_d or best_i == None:
                    best_i = i
                    best_j = j
                    min_d = d
        return best_i, best_j, min_d
                    
    def __merge (self, i, j, d):
        x = self.active_list[i]
        y = self.active_list[j]
        del self.active_list[j]
        del self.active_list[i]
        x.is_active = False
        y.is_active = False
        z = Cluster(self.cluster_count)
        self.cluster_count += 1
        z.children = (x,y)
        z.merge_distance = d
        z.distances = [sys.maxsize for k in range(0, z.index)]
        for other in self.active_list:
            z.distances[other.index] = self.aggregator(x.distance(other), y.distance(other))
        self.active_list.append(z)
        z.is_active = True

    ##  Run it.

    def __call__ (self, utm):
        self.active_list = []
        self.__load_utm(utm)

        while len(self.active_list) > 1:
            i, j, d = self.__best_pair()
            self.__merge(i, j, d)

        return self.active_list[0]



#--  Cluster  ------------------------------------------------------------------

##  A cluster.

class Cluster (object):

    ##  Constructor.

    def __init__ (self, idx, name=None):

        ##  Its index.
        self.index = idx

        ##  Its name.
        self.name = name

        ##  Whether it is active.
        self.is_active = False

        ##  Distances to other clusters.
        self.distances = [None for k in range(0, idx)]

        ##  Subclusters.
        self.children = None

    ##  Look up a distance in the distance matrix.

    def distance (self, other):
        if other.index > self.index: return other.distance(self)
        else: return self.distances[other.index]

    ##  Set the distance between this cluster and another.

    def set_distance (self, other, d):
        if other.index > self.index: other.set_distance(self, d)
        else: self.distances[other.index] = d

    ##  Print out details.

    def dump (self):
        self.__dump1(0)

    def __dump1 (self, indent):
        if self.children:
            print('  ' * indent + '[', self.merge_distance)
            indent += 1
            self.children[0].__dump1(indent)
            self.children[1].__dump1(indent)
            indent -= 1
            print('  ' * indent + ']')
        else:
            print('  ' * indent + self.name)


#-------------------------------------------------------------------------------
# if len(sys.argv) != 3:
#     print '** Usage: (min|max|mean) utm'
#     sys.exit(1)
# 
# if sys.argv[1] == 'min': aggregator = min
# elif sys.argv[1] == 'max': aggregator = max
# elif sys.argv[1] == 'mean': aggregator = mean
# else:
#     print '** Usage: (min|max|mean) utm'
#     sys.exit(1)
# 
# utm = UTM()
# utm.load(sys.argv[2])
# #utm.dump()
# clusterer = Clusterer(aggregator)
# root = clusterer(utm)
# root.dump()
