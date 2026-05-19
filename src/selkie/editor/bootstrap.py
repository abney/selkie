
from .config import in_browser
if in_browser:

    from .ui_bootstrap import *

else:

    def write (*args): pass
    def get_text (*args): pass
    def post_text (*args): pass
    
