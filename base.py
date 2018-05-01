#!/volume1/@appstore/python/bin/python
import argparse
import os, sys
import paramiko
import subprocess
import time
from interruptingcow import timeout
import glob
from argparse import RawTextHelpFormatter

DATADIR= '/volume1/homes/scipionuser/'
EPUDATADIR= 'OffloadData/'
PROJECTDIR='Projects/'
RSYNC='/usr/bin/rsync'

def _usage(description, epilog):
    """ Print usage information and process command line
        returns: project name
                 target directory
                 timeout (stop) seconds
    """
    print "PROJECT NAMES------------------------------"
    projectDir = '/var/services/homes/scipionuser/Projects/20*'
    for name in glob.glob(projectDir):
        print("  ", os.path.basename(name))
    print "USB DISK AVAILABLES"
    projectDir = '/volumeUSB*/usbshare'
    for name in glob.glob(projectDir):
        print("  ", os.path.basename(name))

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter,
                                     epilog=epilog)
    parser.add_argument("projname", help="source directory")
    parser.add_argument("target", help="target directory")
    parser.add_argument("--timeout", help="timeout (default=5, unit=days)",
                        default=5)
    args = parser.parse_args()
    return args.projname, args.target, args.timeout * 24 * 60 * 60 # convert to seconds

def _remote(target):
    """ return  username, host and target dir by parsing target
                if local copy username = host = None
    """
    if "@" in target:
        parse = target.split(":")[0].split("@")
        return parse[0], parse[1], target.split(":")[1]
    else:
        return None, None, target



def _createDirectory(projectName, targetDir, username=None, host=None):
    """ Create directory either local or remote
        data will be copied to  this directory
    """
    dir = os.path.join(targetDir, projectName)

    if username is None: #local rsync
        if not os.path.exists(dir):
            os.makedirs(dir)
    else: # rmote directory creation
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # do not halt is host
                                                                  # is not in known_hosts file
        ssh.connect(host, 22, username, None)
        ssh.exec_command('mkdir -p ' + dir)
        ssh.close
"""
copy_files typeData = list
for data in list
   argsList,append(args

inside while
     for ars in arsList:
"""

def _copy_files(projectName, typeDataList, targetDir, username, host, _timeout):
    """loop that copies files"""
    argsList={} # disctionary with directories to be copied
    for  typeData in typeDataList:
        args = [RSYNC]
        args.append("-va")
        args.append("--progress")
        source = os.path.join(DATADIR, typeData, projectName + "/")
        args.append(source)
        targetDir = os.path.join(targetDir, projectName, typeData)
        if username is not None:
            args.append("%s@%s:%s" % (username, host, targetDir))
        else:
            args.append(targetDir)
        argsList[typeData] = args



    try:
        with timeout(_timeout, exception=RuntimeError): # _timeout seconds
            while True:
                for typeData in typeDataList:
                    rsyncproc = subprocess.Popen(argsList[typeData])
                print "sleeping";sys.stdout.flush()
                time.sleep(900)
                print "weaking up";sys.stdout.flush()

    except RuntimeError:
        print "Aborting, copy didn't finish within %d seconds" % _timeout

    exitcode = rsyncproc.wait()
    return exitcode
