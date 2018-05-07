#!/volume1/@appstore/python/bin/python
import argparse
import os, sys
import paramiko
import time
from interruptingcow import timeout
import glob
from argparse import RawTextHelpFormatter
import select

DATADIR= '/volume1/homes/scipionuser/'
EPUDATADIR= 'OffloadData/'
PROJECTDIR='Projects/'
RSYNC='/usr/bin/rsync'
SCIPIONHOST = 'scipionbox'
RUSKAHOST = 'ruska'
SCIPIONUSER = 'scipionuser'
SCIPIONDATADIR = '/home/%s/ScipionUserData' % SCIPIONUSER
LOGS='Logs'
SLEEPTIME=3600 # seconds

def _usage(description, epilog):
    """ Print usage information and process command line
        returns: project name
                 target directory
                 timeout (stop) seconds
    """
    # Print directory information
    print "PROJECT NAMES------------------------------"
    projectDir = '/var/services/homes/scipionuser/Projects/20*'
    for name in glob.glob(projectDir):
        print "  ", os.path.basename(name)
    print "USB DISK AVAILABLES------------------------"
    usbDir = '/volumeUSB*/usbshare'
    for name in glob.glob(usbDir):
        print "  ", name

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter,
                                     epilog=epilog)
    parser.add_argument("projname", help="source directory")
    parser.add_argument("target", help="target directory")
    parser.add_argument("--timeout", help="timeout (default=5, unit=days)",
                        default=5., type=float)
    args = parser.parse_args()
    return args.projname, args.target, int(args.timeout * 24 * 60 * 60) # convert days to seconds

class RemoteCommands:
    "class to execute a multiple commands in a remote host"
    def __init__(self, retry_time=0):
        self.retry_time = retry_time

    def run_cmd(self, username, host_name, cmd_list):
        i = 0
        while True:
            print("Trying to connect to %s (%i/%i)" % (host_name, i, self.retry_time))
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print "connect to", host_name
                ssh.connect(host_name, username=username)
                break
            except paramiko.AuthenticationException:
                print("Authentication failed when connecting to %s" % host_name)
                sys.exit(1)
            except:
                print("Could not SSH to %s, waiting for it to start" % host_name)
                i += 1
                time.sleep(2)

        # If we could not connect within time limit
        if i >= self.retry_time:
            print("Could not connect to %s. Giving up" % host_name)
            sys.exit(1)
        # After connection is successful
        # Send the command
        for command in cmd_list:
            # print command
            print "> " + command
            # execute commands
            stdin, stdout, stderr = ssh.exec_command(command)
            # TODO() : if an error is thrown, stop further rules and revert back changes
            # Wait for the command to terminate
            while not stdout.channel.exit_status_ready():
                # Only print data if there is data to read in the channel
                if stdout.channel.recv_ready():
                    rl, wl, xl = select.select([ stdout.channel ], [ ], [ ], 0.0)
                    if len(rl) > 0:
                        tmp = stdout.channel.recv(1024)
                        output = tmp.decode()
                        print output
        # Close SSH connection
        ssh.close()
        return


class CopyFiles():

    def __init__(self, projectName, target, timeout):
        self.projectName = projectName
        self.timeout = timeout

        if "@" in target:
            parse = target.split(":")[0].split("@")
            self.targetUserName = parse[0]
            self.targetHost = parse [1]
            self.targetDir = target.split(":")[1]
            self.localTarget = False
        else:
            self.targetUserName = None
            self.targetHost = None
            self.targetDir = target
            self.localTarget = True
        self.remoteCommand = RemoteCommands(2) # retry comamnd 2 times

    def _createDirectory(self, typeData):
        """ Create directory either local or remote
            data will be copied to  this directory
        """
        dir = os.path.join(self.targetDir, self.projectName, typeData)

        if self.localTarget: #save to local usb disk
            if not os.path.exists(dir):
                os.makedirs(dir)
        else: # rmote directory creation
            self.remoteCommand.run_cmd(self.targetUserName,
                                       self.targetHost,
                                       ['mkdir -p %s' % dir])

    def _copy_files(self, typeDataList, _timeout):
        """loop that copies files"""

        if  EPUDATADIR in typeDataList:
            typeData = EPUDATADIR
            self._createDirectory(typeData)
            cmdEPU = RSYNC + \
                  " -va" + \
                  " --progress " + \
                  " --log-file=%s " % os.path.join(DATADIR,LOGS,self.projectName)  + \
                  os.path.join(DATADIR, typeData, self.projectName + "/ ")
            targetDir = os.path.join(self.targetDir, self.projectName, typeData)
            if self.localTarget:
                cmdEPU += targetDir
            else:
                cmdEPU += "%s@%s:%s" % (self.targetUserName, self.targetHost, targetDir)

        if PROJECTDIR in typeDataList:
            typeData = PROJECTDIR
            self._createDirectory(typeData)
            cmdProj = RSYNC + \
                  " -va" + \
                  " --progress " + \
                  ' --exclude="*Fractions.mrc" ' + \
                  " --log-file=%s " % os.path.join(DATADIR,LOGS,self.projectName)  + \
                  os.path.join(DATADIR, typeData, self.projectName + "/ ")
            targetDir = os.path.join(self.targetDir, self.projectName, typeData)
            if self.localTarget:
                cmdProj += targetDir
            else:
                cmdProj += "%s@%s:%s" % (self.targetUserName, self.targetHost, targetDir)
            """
            typeData = PROJECTDIR
            self._createDirectory(typeData)
            cmdProj = RSYNC + \
                  " -va" + \
                  " --progress" + \
                  " " + SCIPIONDATADIR + "/projects/" + self.projectName + "/ "
            targetDir = os.path.join(self.targetDir, self.projectName, typeData)
            if self.localTarget:
                cmdProj += "%s@%s:%s" % (SCIPIONUSER, RUSKAHOST, targetDir)
            else:
                cmdProj += "%s@%s:%s" % (self.targetUserName, self.targetHost, targetDir)
            """

        try:
            with timeout(_timeout, exception=RuntimeError): # _timeout seconds
                while True:
                    if EPUDATADIR in typeDataList:
                        print cmdEPU
                        os.system(cmdEPU)
                    if PROJECTDIR in typeDataList:
                        print cmdProj
                        os.system(cmdProj)
                        #self.remoteCommand.run_cmd(SCIPIONHOST, [cmdProj])
                    print "sleeping";sys.stdout.flush()
                    time.sleep(SLEEPTIME)
                    print "weaking up";sys.stdout.flush()

        except RuntimeError:
            print "Aborting, copy didn't finish within %d seconds" % _timeout

