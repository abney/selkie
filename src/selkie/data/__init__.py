
from os.path import join
from importlib.resources import files

def path (*names):
    return join(__spec__.submodule_search_locations[0], *names)

def ex (*names):
    return path('examples', *names)
