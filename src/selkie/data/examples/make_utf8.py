import codecs

s = '''Latin A: A
Latin M: M
a acute: \u00e1
engma: \u014b
barred lambda: \u019b
belted ell: \u026c
ayin: \u02c1
pi: \u03c0
Cyrillic a: \u0430
Cyrillic zhe: \u0436
Armenian cheh: \u0543
aleph: \u05d0
Tibetan ta: \u0f4f
Coptic 3 bar: \u2cb6
Japanese no: \u306e
Chinese 2: \u4e8c
Old Italic C: \ud800\udf02
Gothic A: \ud800\udf30
'''
file = codecs.getwriter('utf8')(open('utf8.txt', 'w'))
file.write(s)
file.close()
