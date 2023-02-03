##  \package seal.script.cld
#   Managing CLD application files.

import sys
from io import StringIO
from os.path import exists, abspath, join
import seal
from seal.core.misc import Shift
from seal.core.sh import mkdir, cp
from seal.core.io import pprint, ex
from seal.cld.toplevel import CLDManager


#--  Main  ---------------------------------------------------------------------

#
#  !  obligatory argument
#  ?  optional argument; will not accept -FLAG or KEY=VALUE
#  =  list of KEY=VALUE assignments
#  *  list of remaining arguments
#  @  keyword arguments (KEY=VALUE)
#
# _commands = {
#     'call': (com_call, '!='),
#     'config': (com_config, ''),
#     'create': (com_create, ''),
#     'create_cgi': (com_create_cgi, '?@'),
#     'create_test': (com_create_test, ''),
#     'delete': (com_delete, '*'),
#     'export': (com_export, '!*'),
#     'glab': (com_glab, '!*@'),
#     'group': (com_group, '*@'),
#     'import': (com_import, '!*'),
#     'info': (com_info, '?'),
#     'list': (com_list, '*'),
#     'ls': (com_ls, '?'),
#     'perm': (com_perm, '*'),
#     'rm': (com_rm, '!@'),
#     'run': (com_run, '@'),
#     'set': (com_set, '='),
#     'tree': (com_tree, '@'),
#     'unset': (com_unset, '*'),
#     'user': (com_user, '???@')
#     }
# 
# _commands['cfg'] = _commands['config']
# _commands['-c'] = _commands['create']
# _commands['-l'] = _commands['list']
# _commands['del'] = _commands['delete']
# _commands['-d'] = _commands['delete']
# _commands['-e'] = _commands['export']
# _commands['-i'] = _commands['import']
# 
# _flags = {'-u': 'desktop_user',
#           '-M': 'media_dir'}
# 
# _usage = '''Usage:
# cld CFN [KW*]
# cld CFN [KW*] call PATH [KVPAIR*]
# cld CFN [KW*] config
# cld CFN [KW*] create|-c
# cld CFN [KW*] create_cgi CGIFN [KW*]
# cld CFN [KW*] create_test
# cld CFN [KW*] delete|-d [LANG] [ITEM*]
# cld CFN [KW*] export|-e EFN [LANG] [ITEM*]
# cld CFN [KW*] import|-i EFN
# cld CFN [KW*] list|-l [ITEM*]
# cld CFN [KW*] run
# cld CFN [KW*] set [KW*]
# cld CFN [KW*] tree [KW*]
# cld CFN [KW*] unset [KEY*]
# 
# The cld module manages the CLD application and associated 
# application files.  The first argument ('CFN') is an
# application file.  The second argument is the command.
# If there is no command, it defaults to 'run'.  The argument
# types are:
# 
#    CGIFN   the filename of a CGI file
#    EFN     the filename of an export file
#    LANG    a language code
#    ITEM    an item ID
#    KVPAIR  a key-value pair; allows duplicate keys
#    KW      a key-value pair; does not allow duplicate keys
#    KEY     a configuration key
# 
# 
# --  COMMANDS  ----------------------------------------------
# 
# call
#     Instantiate the app and run it.  That is, run
#     Python web server that calls back to the app to
#     handle requests.  Then, for each PATH, execute
#     an HTTP request to the server.  This emulates
#     what a web browser does.  Finally, the HTTP
#     response is printed out.
#     
# config
#     Print out the app configuration.
# 
# create
#     Create the named corpus directory.
# 
# create_cgi
#     Create a CGI file that uses the named corpus.
# 
# create_test
#     Creates a test corpus.  Prepopulates it from seal/examples/corp1.ef.
#     Also creates a media directory.  If not otherwise specified, the
#     media directory will be called 'media' in the current directory.
# 
# delete
#     Delete the indicated items.
# 
# export
#     Export the indicated items to EFN.  If no items are named, the entire
#     corpus is exported.
# 
# import
#     Import from EFN.
# 
# list
#     List the named items.  If none are specified, list the entire corpus.
# 
# run
#     Run the CLD application.  This is the default, if no command is provided.
# 
# set
#     Set values of configuration keys.
# 
# tree
#     Print out the contents of the corpus in tree format.
# 
# unset
#     Unset values of configuration keys.
# '''



# ##  Main function.
# #   A corpus is viewed as a collection of <b>containers</b> whose contents
# #   are <b>items</b>.  An item's ID is unique within its container, but
# #   not necessarily unique within the corpus.
# 
# def main (*args):
#     
#     with Shift(args) as shift:
#     
#         shift.set_usage(_usage)
#     
#         f = None
#         argnames = None
#         args = []
#         kwargs = {}
#         
#         corpus_fn = shift()
#         if corpus_fn in _commands:
#             command = corpus_fn
#             args.append(None)
#         else:
#             cfg = {}
#             if '=' in corpus_fn:
#                 (k,v) = corpus_fn.split('=')
#                 cfg[k] = v
#                 corpus_fn = None
#             for (k,v) in _items(shift):
#                 cfg[k] = v
#             if corpus_fn:
#                 cfg['application_file'] = corpus_fn
#             args.append(cfg)
#             command = shift.ifable()
#             if command is None:
#                 command = 'run'
#             if command not in _commands:
#                 shift.error('Unrecognized command: %s' % repr(command))
# 
#         (f, argnames) = _commands[command]
# 
#         for c in argnames:
#             if c == '!':
#                 arg = shift()
#                 if (arg.startswith('-') and arg != '-') or '=' in arg:
#                     shift.error('Flag or keyword, expecting required argument: %s' % arg)
#                 args.append(arg)
#             elif c == '?':
#                 arg = shift.peek()
#                 if arg and not arg.startswith('-') and '=' not in arg:
#                     args.append(shift())
#             elif c == '=':
#                 args.extend(_items(shift))
#             elif c == '*':
#                 args.extend(shift.rest())
#             elif c == '@':
#                 kwargs.update(_items(shift))
#             else:
#                 shift.error('Bad argument spec: %s' % repr(c))
# 
#     f(*args, **kwargs)
#     
# 
# def _dict (shift):
#     return dict(_items(shift))
# 
# def _items (shift):
#     while True:
#         arg = shift.peek()
#         if arg is None:
#             break
#         elif '=' in arg:
#             shift()
#             yield arg.split('=')
#         elif arg.startswith('-'):
#             shift()
#             key = _flags[arg]
#             value = shift()
#             yield (key, value)
#         else:
#             break


if __name__ == '__main__':
    CLDManager.__main__(sys.argv)
