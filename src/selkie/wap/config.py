
from importlib.util import find_spec
in_browser = bool(find_spec('js'))
tornado_available = bool(find_spec('tornado'))
