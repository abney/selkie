##  \package seal.script.auth
#   Managing authentication files (users.txt, sessions.txt).

import os, sys
from seal.core.misc import shift
from seal.app.auth import LocalAuthenticator


_usage = '''auth COM [USER]

Examples:

    auth ls          # list users
    auth set foo     # sets password for foo (prompts for password)
    auth check foo   # checks password (prompts for password)
    auth delete foo  # deletes entry for foo
'''

##  Usage:
#
#       auth COM [USER]
#
#   Examples:
#
#       auth ls          - list users
#       auth set foo     - sets password for foo (prompts for password)
#       auth check foo   - checks password (prompts for password)
#       auth delete foo  - deletes entry for foo

def main ():
    auth = LocalAuthenticator(os.getcwd())

    print('Password file:', auth.passwords().filename)
    print('Sessions file:', auth.sessions().filename)
    print()

    shift.usage = _usage
    com = shift()
    if com == 'ls':
        user = shift.ifable()
        if user:
            auth.print_user(user)
        else:
            auth.list_users()

    elif com == 'set':
        user = shift()
        auth.set_password(user)

    elif com == 'check':
        user = shift()
        auth.print_check(user)

    elif com == 'delete':
        user = shift()
        auth.delete(user)

    else:
        print()

if __name__ == '__main__':
    main()
