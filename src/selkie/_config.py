
import os
from .io import Container

config = Container(os.environ.get('SELKIE_CONFIG') or '~/.selkie')
