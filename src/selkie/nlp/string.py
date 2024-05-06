
import datetime, unicodedata
from io import StringIO
from time import time as now


#--  Strings  ------------------------------------------------------------------

##  Describe each character in a unicode string.

def unidescribe (s):
    for (i,c) in enumerate(s):
        print(i, hex(ord(c)), unicodedata.name(c))


##  A <b>word</b> consists only of alphanumerics and underscore, and
#   is not the empty string.

def isword (s):
    return len(s) > 0 and all(c.isalnum() or c == '_' for c in s)


##  Break the string into its lines.  The lines do not include carriage return
#   and newline.

def lines (s):
    if isinstance(s, (bytes, bytearray)):
        cr = 13
        nl = 10
    else:
        cr = '\r'
        nl = '\n'
    i = 0
    while True:
        k = s.find(nl, i)
        if k < 0: break
        j = k
        if j > i and s[j-1] == cr:
            j -= 1
        yield s[i:j]
        i = k + 1


#--  as_ascii  -------------------------

def _objectionable_codepoint (x):
    return (x < 32 or x == 123 or x == 125 or x >= 127)

def _is_unobjectionable (s):
    if isinstance(s, str):
        for c in s:
            x = ord(c)
            if _objectionable_codepoint(x): return False
        return True
    else:
        return False

_my_names = {7: 'bel',
             8: 'bs',
             9: 'tab',
             10: 'nl',
             11: 'vt',
             12: 'ff',
             13: 'ret',
             27: 'esc',
             123: 'lb',
             125: 'rb',
             127: 'del',
             8211: 'end', # 2013
             8212: 'emd', # 2014
             8216: 'lsq', # 2018
             8217: 'rsq', # 2019
             8220: 'ldq', # 201c
             8221: 'rdq'} # 201d

_my_names_inv = None

_substitutions = {9: ' ',    # tab
                  11: '\n',  # vert tab
                  12: '\n',  # form feed
                  8211: '-', # en-dash
                  8212: '-', # em-dash
                  8216: "'", # left single quote
                  8217: "'", # right single quote
                  8220: '"', # left double quote
                  8221: '"'} # right double quote

def _write_name (c, x, out):
    try:
        out.write(unicodedata.name(c))
    except Exception:
        out.write(hex(x)[2:])

def _write_hex (c, x, out):
    s = hex(x)[2:]
    if len(s) == 0:
        raise Exception('Empty hex string')
    elif len(s) == 1:
        out.write('0')
        out.write(s)
    elif len(s) == 2:
        out.write(s)
    else:
        for i in range(4-len(s)):
            out.write('0')
        out.write(s)

##  Convert a string to ASCII.

def as_ascii (s, use='hex'):
    if not isinstance(s, str):
        return as_ascii(str(s), use)
    elif _is_unobjectionable(s):
        return s
    if use in (None, 'alts'):
        with StringIO() as out:
            for c in s:
                x = ord(c)
                if x == 10 or 32 <= x <= 126:
                    out.write(c)
                elif use == 'alts' and x in _substitutions:
                    out.write(_substitutions[x])
            return out.getvalue()
    else:
        if use == 'names': f = _write_name
        elif use == 'hex': f = _write_hex
        else: raise Exception('Bad value for use: %s' % use)
        with StringIO() as out:
            for c in s:
                x = ord(c)
                if _objectionable_codepoint(x):
                    out.write('{')
                    if x in _my_names:
                        out.write(_my_names[x])
                    else:
                        f(c, x, out)
                    out.write('}')
                else:
                    out.write(c)
            return out.getvalue()

##  Undo as_ascii().

def from_ascii (s):
    global _my_names_inv
    if '{' in s:
        out = StringIO()
        i = 0
        while i < len(s):
            c = s[i]
            if c == '{':
                i += 1
                j = s.find('}', i)
                if j < 0:
                    raise Exception("'{' without matching '}'")
                name = s[i:j]
                if name.isdigit():
                    c = chr(int(name, 16))
                else:
                    if _my_names_inv is None:
                        _my_names_inv = {}
                        for (k,v) in _my_names.items():
                            _my_names_inv[v] = chr(k)
                    c = _my_names_inv[name]
                out.write(c)
                i = j+1
            else:
                out.write(c)
                i += 1
        s = out.getvalue()
        out.close()
        return s
    else:
        return s


##  Convert a string to printable ASCII characters.  Here, a "printable"
#   character is a character in the range U+0020 (space) to U+007e inclusive,
#   or newline (U+000a).  That is, space and newline are considered printable,
#   all other whitespace and control characters are not; nor is DEL (U+007f).
#   Use substitutions for "smart quotes" and related characters.  Replace tab
#   with space; replace vertical tab, and formfeed with newline.  Delete all
#   other characters that are not printable ASCII.  Returns an iteration over
#   characters.

def ascii_chars (s):
    for c in s:
        n = ord(c)
        if n in _substitutions:
            yield _substitutions[n]
        elif n >= 0x20 and n <= 0x7e:
            yield c
        elif n == 0x0a:
            yield c

##  Convert a single character to a (possibly escaped) form that is safe for
#   inclusion between double quotes.  Double quotes and backslashes are escaped
#   with backslashes, and newline is replaced with backslash-en.  Returns an
#   iteration over strings.

def quotable_chars (s):
    for c in s:
        if c == '"':
            yield '\\"'
        elif c == '\\':
            yield '\\\\'
        elif c == '\n':
            yield '\\n'
        else:
            yield c

##  Like repr(), but always returns a double-quoted string.  May be called as:
#   quote(ascii_chars(s)).

def quoted (s):
    with StringIO() as f:
        f.write('"')
        for c in quotable_chars(s):
            f.write(c)
        f.write('"')
        return f.getvalue()


#--  deaccent  -------------------------

_deaccent_map = [
    None, None, None, None, None, None, None, None, None, '\t', '\n', None, None, '\r', None, None,
    None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
    ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
    '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
    'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_',
    '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', None,
    None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
    None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
    None, '!', 'c', 'L', 'O', 'Y', None, None, None, 'c', 'a', '<<', '-', None, 'R', None,
    None, '+/-', '2', '3', None, 'm', None, '.', None, '1', 'o', '>>', '1/4', '1/2', '3/4', '?',
    'A', 'A', 'A', 'A', 'A', 'A', 'AE', 'C', 'E', 'E', 'E', 'E', 'I', 'I', 'I', 'I',
    'Dh', 'N', 'O', 'O', 'O', 'O', 'O', '*', 'O', 'U', 'U', 'U', 'U', 'Y', 'Th', 'ss',
    'a', 'a', 'a', 'a', 'a', 'a', 'ae', 'c', 'e', 'e', 'e', 'e', 'i', 'i', 'i', 'i',
    'dh', 'n', 'o', 'o', 'o', 'o', 'o', '/', 'o', 'u', 'u', 'u', 'u', 'y', 'th', 'y'
    ]

##  Map accented characters to their unaccented form.

def deaccent (s):
    asc = []
    for u in s:
        i = ord(u)
        if i >= 0 and i < len(_deaccent_map):
            a = _deaccent_map[i]
            if a:
                asc.append(a)
    return ''.join(asc)


##  Interpret an ASCII string as UTF8.

def utf8 (s, fn=None):
    if fn is None:
        print(' '.join(hex(c)[2:] for c in s.encode('utf8')))
    else:
        with open(fn, 'w', encoding='utf8') as f:
            print(s, file=f)

##  Convert to a boolean value.

def as_boolean (s):
    if s == 'False': return False
    elif s == 'True': return True
    else: raise Exception('Not a boolean: ' + str(s))

##  Convert the string to ASCII and trim it to fit in a field with
#   fixed width w.

def trim (w, s=None):
    if s is None:
        s = w
        w = 0
    s = as_ascii(s, use='hex')
    if w > 0 and len(s) > w: return s[:w]
    else: return s


#--  Date-Time string, Size string  --------------------------------------------

##  Print out a timestamp readably.

def dtstr (timestamp):
    return datetime.datetime.fromtimestamp(timestamp).isoformat().replace('T',' ')

##  Print out a file size readably.

def sizestr (nbytes):
    if nbytes >= 1000000000000000:
        return '%5.3f PB' % (nbytes/1000000000000000)
    elif nbytes >= 1000000000000:
        return '%5.3f TB' % (nbytes/1000000000000)
    elif nbytes >= 1000000000:
        return '%5.3f GB' % (nbytes/1000000000)
    elif nbytes >= 1000000:
        return '%5.3f MB' % (nbytes/1000000)
    elif nbytes >= 1000:
        return '%5.3f KB' % (nbytes/1000)
    else:
        return '%d B' % nbytes


##  Time difference, in human-readable form.

def elapsed_time_str (start, end):
    sign = ''
    if end < start:
        sign = '-'
        (start, end) = (end, start)
    return sign + timestr(end - start)

##  Readable string showing an amount of time.

def timestr (nsec):
    nhr = 0
    nmin = 0
    if nsec < 1:
        return '%.4f ms' % (nsec * 1000)
    if nsec >= 60:
        nmin = int(nsec / 60)
        nsec -= nmin * 60
        if nmin >= 60:
            nhr = int(nmin / 60)
            hstr = int(nhr)
            nmin -= nhr * 60
    intsec = int(nsec)
    fraction = nsec - intsec
    return '%d:%02d:%02d%s' % (nhr, nmin, intsec, ('%.4f' % fraction)[1:])


class Time (object):

    def __init__ (self):
        self.t0 = None

    def __enter__ (self):
        self.t0 = now()

    def __exit__ (self, t, v, tb):
        t1 = now()
        print('Time elapsed (h:mm:ss):', timestr(t1 - self.t0))


#--  Expand environment variables  ---------------------------------------------

def expand_envvars (s):
    out = []
    i = 0
    while True:
        j = s.find('$', i)
        if j < 0:
            if i < len(s):
                out.append(s[i:])
            break
        # s[j] is a $
        if j > i: out.append(s[i:j])
        i = j + 1
        if s[i] == '$':
            out.append('$')
            i += 1
        elif s[i] in '({':
            if s[i] == '(': end = ')'
            else: end = '}'
            i += 1
            j = s.find(end, i)
            name = s[i:j].strip()
            if not name: raise Exception('Empty env var name')
            v = os.environ.get(name)
            if v: out.append(v)
            i = j + 1
        elif s[i].isalpha() or s[i] == '_':
            j = i + 1
            while j < len(s) and (s[j].isalnum() or s[j] == '_'):
                j += 1
            name = s[i:j].strip()
            if not name: raise Exception('Empty env var name')
            v = os.environ.get(name)
            if v: out.append(v)
            i = j
        else:
            raise Exception('Illegal character after $')
    return ''.join(out)


#--  Reflection  ---------------------------------------------------------------

##  Returns a module given its name.
#   May raise ModuleNotFoundError

def string_to_module (s):
    if not s:
        raise Exception('Require nonempty name')
    return import_module(s)

##  Takes a fully-qualified name and gets the object.

def string_to_object (s):
    j = s.rfind('.')
    if j < 0:
        raise Exception('Require fully qualified name')
    m = string_to_module(s[:j])
    return m.__dict__[s[j+1:]]
