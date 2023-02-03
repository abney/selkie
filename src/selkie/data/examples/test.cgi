#!/Users/abney/anaconda3/bin/python

import os

lines = ['%s: %s\r\n' % (k,v) for (k,v) in os.environ.items()]
n = sum(len(l) for l in lines)

print('HTTP/1.1 200 OK', end='\r\n')
print('Content-Type: txt/plain', end='\r\n')
print('Content-Length: %d' % n, end='\r\n')
print(end='\r\n')
for line in lines:
    print(line, end='')
