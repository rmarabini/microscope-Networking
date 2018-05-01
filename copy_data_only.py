#!/volume1/@appstore/python/bin/python
from base import (_copy_files, _createDirectory, _remote,
                  _usage, EPUDATADIR, PROJECTDIR)
import sys

if __name__ == '__main__':
    description = 'Copy Data (no project) files'
    epilog = 'Example: %s 2018_04_16_belen_t7 /volumeUSB2/usbshare/.' % \
             __file__
    epilog += '\nExample: %s 2018_project_blas jmv@hilbert:.' % __file__
    epilog += '\nExample: %s 2018_04_16_belen_t7 /volumeUSB2/usbshare/. ' \
              '--timeout 1' % __file__
    epilog += '\n  where 1 is run for 1 day (5 days is the default)'
    epilog += '\nUMOUNT (as administrator): sudo umount /volumeUSB2/usbshare/' \
              '2018_04_16_belen_t7)'
    projectName, target, timeout = _usage(description, epilog)
    username, host, targetDir = _remote(target)
    _createDirectory(projectName, targetDir, username, host)
    exitcode = _copy_files(projectName,
                           [EPUDATADIR],  # data type to e transfered
                           targetDir,
                           username,
                           host,
                           timeout)

    if exitcode==0:
        pass
    else:
        print("\nWARNING: looks like some error occured :( \n\n")
        sys.exit(1)

    print ("Done")
