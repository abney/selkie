
import readline
from time import time as now
from random import shuffle
from heapq import heappush, heappop
from .object import MapProxy
from .newio import Tabular
from .com import Main


min = 60.00
hr = 60 * min
da = 24 * hr
mo = 30 * da
yr = 365 * da

Durations = (0, 2 * min, 1 * hr, 1 * da, 7 * da, 1 * mo, 1 * yr)


class DrillTable (MapProxy):

    def __init__ (self, user, lg):
        user.disk.mkdir('drill')

        self._file = Tabular(user.disk['drill'][lg])
        self.__map__ = {'__unit__': 0}

        for r in self._file:
            if r[0] == '__unit__':
                self.__map__['__unit__'] = int(r[1])
            else:
                item = Item(self, *r)
                self.__map__[item.key()] = item

    def save (self):
        self._file.store(self.__records__())

    def __records__ (self):
        for (k, v) in self.__map__.items():
            if k == '__unit__':
                yield (k, str(v))
            else:
                yield v.__record__()

    def new_batch (self, items):
        for item in items:
            self.__map__[item.key()] = item
        self.__map__['__unit__'] = self.__map__['__unit__'] + 1
        self.save()


class Item (object):

    def __init__ (self, table, word, gloss, t, d):
        self._table = table
        self._word = word
        self._glosses = gloss.split('|')
        self._t = float(t)
        self._d = int(d)

    def key (self): return self._word
    def word (self): return self._word
    def glosses (self): return self._glosses

    def due (self):
        if self._d < len(Durations):
            return self._t + Durations[self._d]
        else:
            return self._t + Durations[-1]

    def reset_d (self):
        self._d = 0
        self._table.save()

    def incr_d (self):
        self._d += 1
        self._table.save()

    def __eq__ (self, other):
        return (self._word, self._glosses) == (other._word, other._glosses)

    def __lt__ (self, other):
        return self.due() < other.due()

    def __le__ (self, other):
        return self.due() <= other.due()

    def __record__ (self):
        return (self._word, '|'.join(self._glosses), str(self._t), str(self._d))


class Drill (object):

    def __init__ (self, user, corpus, lg):
        self._table = DrillTable(user, lg)
        self._units = list(self.get_units(corpus, lg))
        self._batch = None
        self._heap = sorted(item for item in self._table.values() if isinstance(item, Item))

    def get_units (self, corpus, lg):
        for doc in corpus.langs[lg].get_documents():
            if doc.text_type == 'drill':
                for item in doc.walk():
                    if item.text_type == 'vocab':
                        yield item

    def __call__ (self):
        self._fetch_batch()
        for item in self._batch:
            correct = self._present(item)
            if correct:
                item.incr_d()
            else:
                item.reset_d()

    def next_unit (self):
        return self._table['__unit__']

    def _fetch_batch (self):
        self._batch = batch = []
        T = now()
        if self._heap and self._heap[0].due() <= T:
            print('Review')
            for _ in range(20):
                if self._heap[0].due() > T:
                    break
                batch.append(heappop(self._heap))
        else:
            n = self.next_unit()
            if n < len(self._units):
                print('Unit', n)
                unit = self._units[n]
                for sent in unit:
                    batch.append(Item(self._table, str(sent), sent.translation(), T, 0))
                self._table.new_batch(batch)
        shuffle(batch)
        return batch

    def _present (self, item):
        ans = input(item.word() + ': ')
        g = item.glosses()
        correct = (ans in g)
        if correct:
            print('Yes')
        elif not ans:
            print('; '.join(g))
        else:
            print('No:', '; '.join(g))
        print()
        return correct
