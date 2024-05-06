######################################################################
#                                                                    #
#  Chapter 2                                                         #
#  Input-output                                                      #
#                                                                    #
######################################################################

from nell import *


# 2.1  Input streams  ------------------------------------------------

r = reader(ex.text1)
line = next(r)
line = next(r)

r.location()

try:
    r.error('Fake syntax error')
except IOError as e:
    print(e)


# 2.1.1  Reader and StringReader  ------------------------------------

for line in reader(ex.text1):
    print('<' + line.rstrip() + '>')


for line in StringReader('this\nis a\ntest\n'):
    print('<' + line.rstrip() + '>')



# 2.1.2  TabularFile  ------------------------------------------------

for record in head(tabularfile(ex.t1)):
    print(record)



# 2.1.3  TokenFile  --------------------------------------------------

s = 'def foo (bar=42.0, baz="hi"):'
tf = tokenfile(StringReader(s))
list(tf)[:5]

tf = tokenfile(ex.tok1)
list(tf.items())[:3]
