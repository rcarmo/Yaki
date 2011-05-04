#! /bin/env python

import sys,os
import getpass


def mkuser():
    sys.path.append( os.path.join(os.pardir,os.pardir,os.pardir) )
    from snakeserver.user import LoginUser
    userid=raw_input("enter userid (login): ")
    if not userid:
        raise ValueError("must give userid")
    name=raw_input("enter full user name (may be empty): ")
    directory=raw_input("enter user's root directory: ")
    directory=os.path.abspath(os.path.expanduser(directory))
    if not os.path.isdir(directory):
        raise ValueError("invalid directory")
    else:
        print "(full path=%s)" % directory
    passwd=getpass.getpass("enter password: ")
    passwd2=getpass.getpass("enter password again: ")
    if passwd2!=passwd:
        raise ValueError("passwords don't match")
    
    user=LoginUser(userid, passwd)
    if name:
        name='"%s"' % name
    else:
        name='None'
    print
    print "Add the following line to the webapp's configItems (in the 'knownusers' dict):"
    print '   "%s": FileUser("%s", %s, r"%s", passwordhash="%s"), ' % (userid, userid, name, directory, user.password.encode("hex"))
    print
    

if __name__=="__main__":
    mkuser()
