#!/volume1/@appstore/python/bin/python
import argparse
import os, sys
import paramiko
import time
from interruptingcow import timeout
import glob
from argparse import RawTextHelpFormatter
import select
import fnmatch

DATADIR = '/volume1/homes/scipionuser/'
EPUDATADIR = 'OffloadData/'
PROJECTDIR = 'Projects/'
RSYNC = '/usr/bin/rsync'
SCIPIONHOST = 'scipionbox'
RUSKAHOST = 'ruska'
SCIPIONUSER = 'scipionuser'
SCIPIONDATADIR = '/home/%s/ScipionUserData' % SCIPIONUSER
LOGS ='Logs'
SLEEPTIME = 3600 # seconds

def locate(pattern, root_path, skipPattern=None):
    """ Return recursive list of files in directory root_path
        that match pattern pattern
    """
    for path, dirs, files in os.walk(os.path.abspath(root_path)):
        for filename in fnmatch.filter(files, pattern):
            if skipPattern is not None and filename.endswith(skipPattern):
                continue
            yield os.path.join(path, filename)

def _usage(description, epilog):
    """ Print usage information and process command line
        returns: project name
                 target directory
                 timeout (stop) seconds
    """
    # Print directory information
    print "PROJECT NAMES------------------------------"
    projectDir = '/var/services/homes/scipionuser/Projects/20*'
    for name in sorted(glob.glob(projectDir)):
        print "  ", os.path.basename(name)
    print "USB DISK AVAILABLES------------------------"
    usbDir = '/volumeUSB*/usbshare'
    for name in sorted(glob.glob(usbDir)):
        print "  ", name

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=RawTextHelpFormatter,
                                     epilog=epilog)
    parser.add_argument("projname", help="source directory")
    parser.add_argument("target", help="target directory")
    parser.add_argument("--timeout", help="timeout (default=5, unit=days)",
                        default=5., type=float)
    args = parser.parse_args()
    timeout = int(args.timeout * 24 * 60 * 60) # convert days to seconds

    return args.projname, args.target, timeout


class RemoteCommands:
    "class to execute  multiple commands in a remote host"
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
    """ Copy files generated in either Scipion projects or
        OffloadData (movies) directory
    """
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
        self.remoteCommand = RemoteCommands(2) # retry comand 2 times

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

    def printNumberFiles(self, source, target, dataType, 
                         pattern="*", localTarget = True,
                         skipPattern=None):
        source = source.strip()
        target = target.strip()
        print "----------------------------------"
        print "INFO: There are %d files in SOURCE dir %s that match pattern = %s " % \
             (len([js for js in locate(pattern, source, skipPattern)]),
                     source, pattern)
        if self.localTarget:
             print "INFO: There are %d files in TARGET dir %s that match pattern = %s " % \
                     (len([js for js in locate(pattern, target, skipPattern)]), target, pattern)
        #else:
        #     target = target.split(":")[1]
        #     print 'INFO: Files in REMOTE target dir. Execute in remote host: find ~/%s -name "%s" |wc -l  \n\n REMEMBER that the number_of_files_in_the_target_project_dir = number_files_in_origin_dir - number_of_movies' % (target, pattern)
        #print "Note: During data acquisition the number of files in Source dir will be greater than files in Target dir"
        #if skipPattern is not None:
        #    print "Note: files ending in %s have not been counted since there are links" % skipPattern
        print "----------------------------------"

    def _copy_files(self, typeDataList, _timeout):
        """loop that copies files"""

        logFileName = os.path.join(DATADIR,LOGS,self.projectName)
        if  EPUDATADIR in typeDataList:
            typeData = EPUDATADIR
            self._createDirectory(typeData)
            sourceDirEPU = os.path.join(DATADIR, typeData, self.projectName + "/ ")
            targetDirEPU = os.path.join(self.targetDir, self.projectName, typeData)
            if not self.localTarget:
                targetDirEPU = "%s@%s:%s" % (self.targetUserName, self.targetHost, targetDirEPU)

            cmdEPU = RSYNC + \
                  " -vrlt" + \
                  " --progress " + \
                  " --log-file=%s " % logFileName  + \
                  sourceDirEPU + \
                  targetDirEPU

        if PROJECTDIR in typeDataList:
            typeData = PROJECTDIR
            self._createDirectory(typeData)
            sourceDirProj = os.path.join(DATADIR, typeData, self.projectName + "/ ")
            targetDirProj = os.path.join(self.targetDir, self.projectName, typeData)
            if not self.localTarget:
                targetDirProj = "%s@%s:%s" % (self.targetUserName, self.targetHost, targetDirProj)
            cmdProj = RSYNC + \
                  " -vrlt" + \
                  " --progress --delete " + \
                  ' --exclude="*Fractions.mrc" ' + \
                  " --log-file=%s " % logFileName  + \
                  sourceDirProj + \
                  targetDirProj

        try:
            with timeout(_timeout, exception=RuntimeError): # _timeout seconds
                while True:
                    if EPUDATADIR in typeDataList:
                        typeData = EPUDATADIR
                        print cmdEPU
                        os.system(cmdEPU)
                    if PROJECTDIR in typeDataList:
                        typeData = EPUDATADIR
                        print cmdProj
                        os.system(cmdProj)
                    if EPUDATADIR in typeDataList:
                        self.printNumberFiles(sourceDirEPU,
                                              targetDirEPU, 
                                              typeData, 
                                              pattern="*Fractions.mrc",
                                              localTarget = self.localTarget)
                    if PROJECTDIR in typeDataList:    
                        self.printNumberFiles(sourceDirProj,
                                              targetDirProj,                             
                                              typeData,                                  
                                              pattern="*",
                                              localTarget=self.localTarget,
                                              skipPattern="Fractions.mrc")
                    print "sleeping";sys.stdout.flush()
                    time.sleep(SLEEPTIME)
                    print "weaking up";sys.stdout.flush()
                    if self.localTarget:
                        pass
        except RuntimeError:
            print "Aborting, copy didn't finish within %d seconds" % _timeout

