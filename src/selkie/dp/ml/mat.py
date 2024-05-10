##  @package seal.ml.mat
#   Deprecated.

from ...cld.seal.io import iter_records


##  Load a matrix.

def load_matrix (fn):
    recs = iter_records(fn, separator=None)
    col_names = next(recs)
    row_names = []
    rows = []
    for rec in recs:
        row_names.append(rec[0])
        rows.append([float(x) for x in rec[1:]])
    return Matrix(rows, row_names=row_names, col_names=col_names)


##  A sparse matrix.

class Matrix (object):

    ##  Cosntructor.

    def __init__ (self, rows, row_names=None, col_names=None):

        ##  Rows.
        self.rows = rows

        ##  Row names.
        self.row_names = row_names

        ##  Column names.
        self.col_names = col_names

        if row_names:
            ##  Row name to row index.
            self.row_dict = {}
            for i, name in enumerate(row_names):
                self.row_dict[name] = i
        else:
            self.row_names = [str(i) for i in range(len(self.rows))]

        if col_names:
            ##  Col name to col index.
            self.col_dict = {}
            for i, name in enumerate(col_names):
                self.col_dict[name] = i

    def __digest_addr (self, addr):
        i, j = addr
        if isinstance(i, str):
            i = self.row_dict[i]
        if isinstance(j, str):
            j = self.col_dict[j]
        return i, j

    ##  Get the value at the given address.

    def __getitem__ (self, addr):
        i, j = self.__digest_addr(addr)
        return self.rows[i][j]

    ##  Set the value.

    def __setitem__ (self, addr, value):
        i, j = self.__digest_addr(addr)
        self.rows[i][j] = value

    ##  String representation.

    def __str__ (self):
        n = len(self.rows[0])
        rng = list(range(n))
        colwidths = [0 for i in rng]
        for row in self.rows:
            for j in rng:
                w = len(str(row[j]))
                if w > colwidths[j]:
                    colwidths[j] = w
        w0 = 0
        for name in self.row_names:
            w = len(name)
            if w > w0: w0 = w

        lines = []
        if self.col_names:
            hdrs = [' ' * (w0 + 1)]
            hdrs += ['%*s' % (colwidths[j], self.col_names[j]) for j in rng]
            lines.append(' '.join(hdrs))
        for i in range(len(self.rows)):
            row = self.rows[i]
            cells = ['%*s:' % (w0, self.row_names[i])]
            for j in rng:
                cells.append('%*s' % (colwidths[j], str(row[j])))
            lines.append(' '.join(cells))
        
        return '\n'.join(lines)
