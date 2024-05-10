'''
Functions for generating xterm control strings.
'''

'''
Dict mapping color names to escape strings for foreground colors.
'''
fg = {'black': '\033[30m',
      'red': '\033[31m',
      'green': '\033[32m',
      'yellow': '\033[33m',
      'blue': '\033[34m',
      'magenta': '\033[35m',
      'cyan': '\033[36m',
      'white': '\033[37m',
      'default': '\033[39m'}

'''
Dict mapping color names to escape strings for background colors.
'''
bg = {'black': '\033[40m',
      'red': '\033[41m',
      'green': '\033[42m',
      'yellow': '\033[43m',
      'blue': '\033[44m',
      'magenta': '\033[45m',
      'cyan': '\033[46m',
      'white': '\033[47m',
      'default': '\033[49m'}

def black (s):
    '''
    Returns a string that displays the contents in black.
    '''
    return fg['black'] + s + fg['default']

def red (s):
    '''
    Returns a string that displays the contents in red.
    '''
    return fg['red'] + s + fg['default']

def green (s):
    '''
    Returns a string that displays the contents in green.
    '''
    return fg['green'] + s + fg['default']

def yellow (s):
    '''
    Returns a string that displays the contents in yellow.
    '''
    return fg['yellow'] + s + fg['default']

def blue (s):
    '''
    Returns a string that displays the contents in blue.
    '''
    return fg['blue'] + s + fg['default']

def magenta (s):
    '''
    Returns a string that displays the contents in magenta.
    '''
    return fg['magenta'] + s + fg['default']

def cyan (s):
    '''
    Returns a string that displays the contents in cyan.
    '''
    return fg['cyan'] + s + fg['default']

def white (s):
    '''
    Returns a string that displays the contents in white.
    '''
    return fg['white'] + s + fg['default']

def cursor_right (n=1):
    '''
    An escape string that moves the cursor n spaces to the right.
    '''
    return '\033%dC' % n

def cursor_left (n=1):
    '''
    An escape string that moves the cursor n spaces to the left.
    '''
    return '\033%dD' % n

def goto_column (n):
    '''
    An escape string that moves the cursor to column n.
    '''
    return '\033%dG' % n

