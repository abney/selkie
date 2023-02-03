##  @package seal.app.parse
#   Provides parse_config() and parse_request().

from os.path import join
from seal.app.config import Config

#
#  parse_request is here rather than in Request because parse_request is needed
#  by digest_environ in seal.app.env, which feeds seal.app.request.
#


#--  parse_config  -------------------------------------------------------------

##  Parse a list of configuration settings.
#   It passes through a Config unchanged.  Otherwise, a Config is created as
#   follows.  First, a list of key-value pairs is constructed.
#    - the basic unit is a string
#      of form "key=value".
#    - A string containing commas is first broken at the commas.
#    - If the string does not contain an '=', it is treated as the value for
#      the key 'settings'.
#    - If s is a dict or Config, its items are used.
#    - If s is a tuple or list, each member is processed.
#    - If None is encountered, it is ignored.
#    - If anything else is encountered, it is assumed to be the app, and is
#      treated as the value of 'app'.
#   The list of key-value pairs is then converted to a Config.

def parse_config (*sources, provenance=None, defaults=None):
    cfn = None
    d = {}
    todo = list(sources)
    i = 0
    while i < len(todo):
        s = todo[i]
        i += 1
        if isinstance(s, str):
            fields = s.split(',')
            if '=' not in fields[0]:
                value = fields[0]
                if value.endswith('.cfg'):
                    cfn = value
                else:
                    d['application_file'] = value
                fields = fields[1:]
            for field in fields:
                item = field.split('=')
                if len(item) != 2:
                    raise Exception('Bad item: %s in %s' % (item, s))
                d[item[0]] = item[1]
        elif isinstance(s, (dict, Config)):
            for (k,v) in s.items():
                d[k] = v
        elif isinstance(s, (tuple, list)):
            todo.extend(s)
        elif s is None:
            pass
        else:
            # assume it's an application
            d['app'] = s
    if cfn is None:
        afn = d.get('application_file')
        if afn:
            cfn = join(afn, '_config')
            d['config_file'] = cfn
    return Config(cfn, d, provenance, defaults)


#--  parse_request  ------------------------------------------------------------

##  Parse a request.  This dispatches to parse_request_string() or 
#   parse_request_tuple() depending on whether the input is a string
#   or tuple/list.  Singleton tuples/lists are first stripped away.

def parse_request (req):
    orig = req

    while isinstance(req, (tuple, list)) and len(req) == 1:
        req = req[0]

    try:
        if isinstance(req, str):
            return parse_request_string(req)
        elif isinstance(req, (list, tuple)):
            return parse_request_tuple(req)
        else:
            raise Exception('Cannot parse request: %s' % repr(req))

    except Exception as e:
        print('** Failure parsing request: %s' % repr(orig))
        raise


##  Parse a request string.

def parse_request_string (s):
    parts = s.split(':')
    if len(parts) == 1:
        return parts[0]
    else:
        pathname = parts[0]
        form = _multidict(_parse_keyvalue_pair(x) for x in parts[1].split(','))
        if len(parts) > 2:
            cookie = dict(_parse_keyvalue_pair(x) for x in parts[2].split(','))
            if len(parts) > 3:
                raise Exception('Too many colons')
        else:
            cookie = {}
        return (pathname, form, cookie)

def _multidict (items):
    d = {}
    for (k,v) in items:
        if k in d:
            d[k].append(v)
        else:
            d[k] = [v]
    return d

def _parse_keyvalue_pair (s):
    i = s.find('=')
    if i < 0:
        key = s
        value = ''
    else:
        key = s[:i]
        value = s[i+1:]
    return (key, value)


##  Parse a request tuple or list.

def parse_request_tuple (req):
    pathname = req[0]
    if len(req) > 1:
        form = _multidict(req[1])
    else:
        form = {}
    if len(req) > 2:
        cookie = dict(req[2])
    else:
        cookie = {}
    return (pathname, form, cookie)


##  Version of cookie information suitable for logging.
#   Argument may be a dict or a Cookie.

def cookie_log_string (cookie):
    if cookie is None:
        return 'None'
    else:
        out = []
        for (k,v) in cookie.items():
            try:
                if k == 'token':
                    if v:
                        v = '<%d chars>' % len(v)
                    else:
                        v = repr(v)
                else:
                    v = repr(v)
            except:
                v = '<error in formatting>'
            out.append('%s: %s' % (k,v))
        return '{' + ', '.join(out) + '}'
