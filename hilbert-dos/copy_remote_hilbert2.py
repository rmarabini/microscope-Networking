#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import os, sys
import glob
import time
from argparse import RawTextHelpFormatter
from base import DATADIR, EPUDATADIR, PROJECTDIR
from sshpubkeys import SSHKey, AuthorizedKeysFile
from sshpubkeys.exceptions import (InvalidKeyError)

SCIPIONUSERPATH = '/home/scipionuser'
DATAPATH = os.path.join(SCIPIONUSERPATH, 'data')
TIMEOUT = 1

def _usage(description, epilog):
    """ Print usage information and process command line
        returns: project name
                 target directory
                 timeout (stop) seconds
    """
    # Print directory information
    print ("PROJECT NAMES-----------------------------")
    projectDir = os.path.join(DATAPATH, EPUDATADIR[:-1], '20*')
    for name in sorted(glob.glob(projectDir)):
        print (os.path.basename(name))

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter,
                                     epilog=epilog)
    parser.add_argument("projname", help="source directory")
    parser.add_argument("keyfile", help='file with public key')
    args = parser.parse_args()
    return args.projname, args.keyfile

if __name__ == '__main__':
    description = 'Allow project to be accessed from outside'
    epilog = 'Example: %s 2018_04_16_belen_t7 /tmp/idrsa_pub' % __file__
    projectName, pubKeyFileName = _usage(description, epilog)
    projectPath = os.path.join(DATAPATH, projectName)

    # create main directory
    if os.path.exists(projectPath):
        print("WARNING: Directory %s already exists." % \
              projectPath)
        time.sleep(TIMEOUT)
    else:
        os.system("mkdir %s" % projectPath)
        os.system("chown scipionuser %s" % projectPath)

    # create offloaddata and project directories
    dir = os.path.join(projectPath, EPUDATADIR[:-1])
    if os.path.exists(dir):
        print("WARNING: Directory %s already exists."% dir)
        time.sleep(TIMEOUT)
    else:
        os.system("mkdir %s" % dir)
        os.system("chown scipionuser %s" % dir)
    #
    dir = os.path.join(projectPath, PROJECTDIR[:-1])
    if os.path.exists(dir):
        print("WARNING: Directory %s already exists."% dir)
        time.sleep(TIMEOUT)
    else:
        os.system("mkdir %s" % dir)
        os.system("chown scipionuser %s" % dir)
    
    # mount data and project
    source1 = os.path.join(DATAPATH, EPUDATADIR, projectName)
    target1 = os.path.join(projectPath, EPUDATADIR, projectName)
    if os.path.exists(target1):
        print("WARNING: %s directory already exists" % target1)
        time.sleep(TIMEOUT)
    else:
        os.symlink(source1, target1)
    #
    source2 = os.path.join(DATADIR, PROJECTDIR, projectName)
    target2 = os.path.join(projectPath, PROJECTDIR, projectName)
    if os.path.exists(target2):
        print("WARNING: %s directory already mounted" % target2)
        time.sleep(TIMEOUT)
    else:
        os.symlink(source2,target2)
    
    # read local public key file
    with open(pubKeyFileName, 'r') as keyFile:
        newKeyString = keyFile.read()
    newKey = SSHKey(newKeyString)
    try:
        newKey.parse()
    except InvalidKeyError as err:
        print("Invalid key:", err)
        sys.exit(1)
    except NotImplementedError as err:
        print("Invalid key type:", err)
        sys.exit(1)

    comment = newKey.comment # key owner 'roberto@flemming'
    print("Adding %s key" % comment)

    # read chrooted authorized_keys file
    authorizedKeyFile = os.path.join(SCIPIONUSERPATH,
                                           '.ssh', 'authorized_keys')
    f = open(authorizedKeyFile, 'r')
    oldKeys = AuthorizedKeysFile(f)

    for key in oldKeys.keys:
        if key.comment == comment:
            print ("key for user %s already exists"%comment)
            print ("I cannot add a second key for the same user/machine")
            print ("You may edit  file %s and delete the old entry" % \
                  os.path.join(SCIPIONUSERPATH,
                               '.ssh',
                                'authorized_keys'))
            exit(1)

    # add new key
    command = 'command="/usr/share/doc/rsync/scripts/rrsync -ro ' \
              '%s",' \
              'no-agent-forwarding,' \
              'no-port-forwarding,' \
              'no-pty,no-user-rc,no-X11-forwarding ' % projectPath
    fullkey = command + newKey.keydata # + newKey.comment
    with open(authorizedKeyFile, 'a') as authorizedFile:
        authorizedFile.write(fullkey)
    # REmemeber
    print("\n\n\n\nREMEMBER, when done: ")
    print("    unmount shared dir1: umount %s "%target1)
    print("    unmount shared dir2: umount %s "%target2)
    print("    delete remote user's public key from file " \
          "%s/.ssh/authorized_keys" % \
          SCIPIONUSERPATH)
    print("IMPORTANT: remote user should save in a file and execute" \
          " the following python code:\n\n\n ")
    print("""
#!/usr/bin/env python
import time
import os

timeout = 60 * 60 * 24 * 5  # retry for 5 days
sleep_time = 60 * 30 # retry each 30 minutes
timeout_start = time.time() # time at which the script was started
command = 'rsync --progress -rlvt -e "ssh -p 2222" scipionuser@ruska.cnb.csic.es:. %s'

while time.time() < timeout_start + timeout:
    os.system(command)
    time.sleep(sleep_time)

# For example:
#     rsync --progress -rlvt -e 'ssh -p 2222' scipionuser@ruska.cnb.csic.es:. --exclude OffloadData localPath 
# NOTE: If you only need to copy the data or the project  modify the above rsync command
# by adding "--exclude OffloadData" if you only want to copy the Project or
# "--exclude Project" if you only want to copy the data
"""%projectName)
