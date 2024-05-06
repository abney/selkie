##  @package seal.core.xterm
#   XTerm-related functions.

##  Dict mapping color names to escape strings.
fg = {'black': '\033[30m',
      'red': '\033[31m',
      'green': '\033[32m',
      'yellow': '\033[33m',
      'blue': '\033[34m',
      'magenta': '\033[35m',
      'cyan': '\033[36m',
      'white': '\033[37m',
      'default': '\033[39m'}

##  Dict mapping color names to escape strings.
bg = {'black': '\033[40m',
      'red': '\033[41m',
      'green': '\033[42m',
      'yellow': '\033[43m',
      'blue': '\033[44m',
      'magenta': '\033[45m',
      'cyan': '\033[46m',
      'white': '\033[47m',
      'default': '\033[49m'}

##  Returns a string that displays the contents in black.
def black (s):
    return fg['black'] + s + fg['default']

##  Returns a string that displays the contents in red.
def red (s):
    return fg['red'] + s + fg['default']

##  Returns a string that displays the contents in green.
def green (s):
    return fg['green'] + s + fg['default']

##  Returns a string that displays the contents in yellow.
def yellow (s):
    return fg['yellow'] + s + fg['default']

##  Returns a string that displays the contents in blue.
def blue (s):
    return fg['blue'] + s + fg['default']

##  Returns a string that displays the contents in magenta.
def magenta (s):
    return fg['magenta'] + s + fg['default']

##  Returns a string that displays the contents in cyan.
def cyan (s):
    return fg['cyan'] + s + fg['default']

##  Returns a string that displays the contents in white.
def white (s):
    return fg['white'] + s + fg['default']

##  An escape string that moves the cursor n spaces to the right.
def cursor_right (n=1):
    return '\033%dC' % n

##  An escape string that moves the cursor n spaces to the left.
def cursor_left (n=1):
    return '\033%dD' % n

##  An escape string that moves the cursor to column n.
def goto_column (n):
    return '\033%dG' % n
