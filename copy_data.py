from base import _copy_files, _createDirectory, _remote, _usage
import sys

if __name__ == '__main__':
    usage = 'Copy Data (no project) files'
    usage += '\n Example: %s 2018_04_16_belen_t7 /volumeUSB2/usbshare/.' % __file__
    usage += '\n Example: %s 2018_project_blas jmv@hilbert:.' % __file__
    usage += '\n Example: %s 2018_04_16_belen_t7 /volumeUSB2/usbshare/. 1' % __file__
    usage += '\n where 1 is run for 1 day (5 days is the default)'
    source, target, timeout = _usage(usage)
    username, host, targetDir = _remote(target)
    _createDirectory(targetDir, username, host)
    exitcode = _copy_files(source, targetDir, username, host, timeout)

    if exitcode==0:
        pass
    else:
        print("\nWARNING: looks like some error occured :( \n\n")
        sys.exit(1)

    print ("Done")