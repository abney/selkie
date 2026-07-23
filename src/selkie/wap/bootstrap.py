
from .config import in_browser
if in_browser:

    from .ui_bootstrap import *

else:

    server_proxy = None

print('selkie.wap.bootstrap: in_browser=', in_browser, 'server_proxy=', server_proxy)
