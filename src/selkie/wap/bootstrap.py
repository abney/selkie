
from .config import in_browser
if in_browser:

    from .ui_bootstrap import *

else:

    def write (*items):
        pass

