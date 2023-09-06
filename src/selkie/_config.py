
import os
from .newio import Container

config = Container(os.environ.get('SELKIE_CONFIG') or '~/.selkie')
