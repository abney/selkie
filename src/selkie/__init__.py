
import os, json

__version__ = '0.25'

config = {}

def _load_config ():
    global config
    fn = os.path.expanduser(os.environ.get('SELKIE_CONFIG') or '~/.selkie.json')
    if os.path.exists(fn):
        with open(fn) as f:
            try:
                config = json.load(f)
            except Exception as e:
                print('Warning: unable to load', fn)
                print(e)

_load_config()
