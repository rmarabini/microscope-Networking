#!/volume1/@appstore/python/bin/python
import argparse
import os, sys
import glob
from argparse import RawTextHelpFormatter
from base import DATADIR, EPUDATADIR, PROJECTDIR

REMOTESCIPIONUSERPATH = \
    '/usr/local/debian-chroot/var/chroottarget/home/scipionuser'

def _usage(description, epilog):
    """ Print usage information and process command line
        returns: project name
                 target directory
                 timeout (stop) seconds
    """
    # Print directory information
    print "PROJECT NAMES-----------------------------"
    projectDir = '/var/services/homes/scipionuser/Projects/20*'
    for name in glob.glob(projectDir):
        print "  ", os.path.basename(name)

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter,
                                     epilog=epilog)
    parser.add_argument("projname", help="source directory")
    args = parser.parse_args()
    return args.projname

if __name__ == '__main__':
    description = 'Allow project to be accessed from outside'
    epilog = 'Example: %s 2018_04_16_belen_t7' % __file__
    epilog += "Rememebr to log as administrator and execute script with sudo"
    projectName = _usage(description, epilog)
    chrootedProjectPath = os.path.join(REMOTESCIPIONUSERPATH, projectName)

    # create main directory
    os.system("mkdir %s" % chrootedProjectPath)
    os.system("chown scipionuser %s" % chrootedProjectPath)

    # create offloaddata and project directories
    dir = os.path.join(chrootedProjectPath, EPUDATADIR[:-1])
    os.system("mkdir %s" % dir)
    os.system("chown scipionuser %s" % dir)
    #
    dir = os.path.join(chrootedProjectPath, PROJECTDIR[:-1])
    os.system("mkdir %s" % dir)
    os.system("chown scipionuser %s" % dir)

    # mount data and project
    mountCommand = "mount -o bind"
    remountCommand = "mount -o remount,ro,bind"
    source = os.path.join(DATADIR, EPUDATADIR, projectName)
    target = os.path.join(chrootedProjectPath, EPUDATADIR[:-1])
    os.system("%s %s %s" %(mountCommand, sourcel, target))
    os.system("%s %s %s" %(remountCommand, source, target)) # remount read only
    #
    source = os.path.join(DATADIR, PROJECTDIR, projectName)
    target = os.path.join(chrootedProjectPath, PROJECTDIR[:-1])
    os.system("%s %s %s" %(mountCommand, source, target))
    os.system("%s %s %s" %(remountCommand, source, target)) # remount read only

    # REmemeber
    print "paste remote user's public key into file %s/.ssh/authorized_keys" % \
          REMOTESCIPIONUSERPATH
    print "delete form file old keys"
    print "unmount old shares: umount %s/20XXX/YYYY "% REMOTESCIPIONUSERPATH
    print ("Done")
