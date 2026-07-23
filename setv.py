
import sys
from pathlib import Path

if len(sys.argv) != 4:
    print('Usage examples:')
    print('$ python -m setv 0 26 dev2')
    print('$ python -m setv 0 27 0')
    sys.exit(1)

(_, major, minor, update) = sys.argv

RELEASE = major + '.' + minor
VERSION = RELEASE + '.' + update

files = ['pyproject.toml',
         'setup.cfg',
         'src/selkie/__init__.py',
         'docs/source/conf.py',
         'docs/source/index.rst']

templates = Path('templates')
for fn in files:
    fn = Path(fn)
    print('Generating', fn)
    src = templates/(fn.name)
    with open(src) as f:
        text = f.read()
    text = text.replace('$VERSION', VERSION).replace('$RELEASE', RELEASE)
    with open(fn, 'w') as f:
        f.write(text)
