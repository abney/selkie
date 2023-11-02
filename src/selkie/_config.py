
import os
from .persist import Container

config = Container(os.environ.get('SELKIE_CONFIG') or '~/.selkie')
