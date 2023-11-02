
from os.path import join
from importlib.resources import files

def path (*names):
    '''
    Joins the pathname of the directory of the selkie.data module to the *names*.
    If no *names* are provided, the return value is just the data directory's pathname.
    '''
    return join(__spec__.submodule_search_locations[0], *names)

def ex (*names):
    '''
    Joins *names* to the pathname of the 'examples' subdirectory of the data directory.

    For example:

    >>> from selkie.data import ex
    >>> ex('romtest.rom')[-33:]
    '/selkie/data/examples/romtest.rom'

    '''
    return path('examples', *names)
