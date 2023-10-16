'''
The selkie.string module contains general string-related functionality.
'''

import datetime, unicodedata
from io import StringIO
from time import time as now


#--  Strings  ------------------------------------------------------------------

def unidescribe (s):
    '''Prints out a description of each (Unicode) character in a string.'''
    for (i,c) in enumerate(s):
        print(i, hex(ord(c)), unicodedata.name(c))


def isword (s):
    '''A *word* consists only of alphanumerics and underscore, and is not the empty string.'''
    return len(s) > 0 and all(c.isalnum() or c == '_' for c in s)


def lines (s):
    '''Iterates over the lines in a string. The lines do not include carriage return and newline.'''
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

# The "objectionable" codepoints are non-printable characters, plus the braces.

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


def as_ascii (s, use='alts'):
    '''
    Convert a string to ASCII. Characters that are not printable ASCII characters are treated as follows.

     * If *use* is None, they are deleted.
     * If *use* is 'alts' (the default), they are replaced with ASCII equivalents if possible, and otherwise deleted.
       The printable characters lie in the range from space (inclusive) to DEL (exclusive).
       Tab is replaced with a single space.
       Newline, vertical tab, and form feed are replaced with newline.
       "Smart quotes" (left and right, single and double) are replaced with the ASCII
       single or double quote. Em- and en-dash are replaced with hyphen.
     * If *use* is 'hex', non-printable characters are replaced with hex codes.
     * If *use* is 'names', they are replaced with their names, wrapped in braces.

    '''
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

def from_ascii (s):
    '''This undoes the effects of ``as_ascii()``.'''

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


# Backwards compatibility only
def ascii_chars (s):
    '''
    Deprecated. Backwards compatibility only.
    '''
    return as_ascii(s, use='alts')


def _quotable_chars (s):
    for c in s:
        if c == '"':
            yield '\\"'
        elif c == '\\':
            yield '\\\\'
        elif c == '\n':
            yield '\\n'
        else:
            yield c

def quoted (s):
    '''
    Like ``repr()``, but always returns a double-quoted string.  May be called as:
    ``quoted(as_ascii(s))``.
    '''
    with StringIO() as f:
        f.write('"')
        for c in _quotable_chars(s):
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

def deaccent (s):
    '''
    Maps accented characters to their unaccented form.
    '''
    asc = []
    for u in s:
        i = ord(u)
        if i >= 0 and i < len(_deaccent_map):
            a = _deaccent_map[i]
            if a:
                asc.append(a)
    return ''.join(asc)


#--  Date-Time string, Size string  --------------------------------------------

def dtstr (timestamp):
    '''
    Returns a string that renders a timestamp readably.
    '''
    return datetime.datetime.fromtimestamp(timestamp).isoformat().replace('T',' ')

##  Print out a file size readably.

def sizestr (nbytes):
    '''
    Returns a string representing a file size readably.
    '''
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

def elapsed_time_str (start, end):
    '''
    Returns a readable string showing a time difference.
    '''
    sign = ''
    if end < start:
        sign = '-'
        (start, end) = (end, start)
    return sign + timestr(end - start)

def timestr (nsec):
    '''
    Returns a readable string showing an amount of time.
    '''
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

#--  Expand environment variables  ---------------------------------------------

def expand_envvars (s):
    '''
    Expands out environment variables. Environment variables begin with dollar
    sign and are optionally enclosed in braces.
    '''
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
