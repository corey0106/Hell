#!/usr/bin/env python
"""
hellanzb - hella nzb

TODO:
o use optparse
o clean up the configuration options, possibly putting them in another file (that would
lie in /etc). ideally most of those settings could be overwritten via the cmd line

@author pjenvey, bbangert

"""

import os, sys, Hellanzb, Hellanzb.Troll, Hellanzb.Ziplick
from Hellanzb.Troll import debug, defineMusicType, error, FatalError

__id__ = "$Id"

def usage():
    pass

def loadConfig():
    """ Load the configuration file """
    confDirs = [ sys.prefix + os.sep + "etc", os.getcwd() + os.sep + "etc", os.getcwd() ]
    
    foundConfig = False
    for dir in confDirs:
        try:
            execfile(dir + os.sep + "hellanzb.conf")
            foundConfig = True
            debug("Found config file in directory: " + dir)
        except IOError, ioe:
            pass

    if not foundConfig:
        error("Could not find configuration file in the following dirs: " + str(confDirs))
        sys.exit(1)

def runDaemon():
    """ start the daemon """
    daemon = Hellanzb.Ziplick.Ziplick()

    daemon.start()

def runTroll():
    """ run troll as a cmd line app """
    try:
        if len(sys.argv) < 2:
            usage()
            sys.exit(1)
                
        archiveDir = sys.argv[1]

        Hellanzb.Troll.init()
        Hellanzb.Troll.troll(archiveDir)

    except FatalError, fe:
        Hellanzb.Troll.cleanUp(incomingDir)
        error("An unexpected problem occurred: " + fe.message + "\n")
        sys.exit(1)

    
if __name__ == '__main__':

    loadConfig()

    exe = os.path.basename(sys.argv[0])
    if exe == "hellanzb":
        runDaemon()
        
    elif exe == "troll":
        runTroll()
