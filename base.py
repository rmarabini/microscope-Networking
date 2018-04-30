import argparse
import os, sys
import paramiko
import subprocess
import time
from interruptingcow import timeout

def _usage(usage):
    """ Print usage information"""
    projectDir = '/var/services/homes/scipionuser/Projects'
    for root, dirs, files in os.walk(projectDir):
        for dir in dirs:
            print(dir)

    parser = argparse.ArgumentParser(usage)
    parser.add_argument("source", help="source directory")
    parser.add_argument("target", help="target directory")
    parser.add_argument("--timeout", help="timeout (default=432000, 5 days)", default=432000)
    args = parser.parse_args()
    return args.source, args.target, args.timeout

def _remote(target):
    """ return tru is target has the symbol @ (remote rsync)"""
    if "@" in target:
        parse = target.split(":")[0].split("@")
        return parse[0], parse[1], target.split(":")[1]
    else:
        return None, None, target

def _createDirectory(dir, username=None, host=None):
    """ Create directory either local or remote"""
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

def _copy_files(source, targetDir, username, host, _timeout):
    """loop that copies files"""
    args = ["/usr/bin/rsync"]
    args.append("-va")
    args.append("--progress")
    args.append(source)
    if username is not None:
        args.append("%s@%s:%s" % (username, host, targetDir))
    else:
        args.append(targetDir)

    try:
        with timeout(_timeout, exception=RuntimeError): # _timeout seconds
            while True:
                print "executing " + ' '.join(args);sys.stdout.flush()
                rsyncproc = subprocess.Popen(args)
                print "sleeping";sys.stdout.flush()
                time.sleep(900)
                print "weaking up";sys.stdout.flush()

    except RuntimeError:
        print "didn't finish within %d seconds" % _timeout

    exitcode = rsyncproc.wait()
    return exitcode
