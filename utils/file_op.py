from utils import common
import os, sys, re, shutil, stat

if 'nt' == os.name:
    from pywintypes import error as pywinerror
    import win32file

if 'posix' == os.name:
    from core.exceptions import WindowsError
    pywinerror = WindowsError

def listdir(directory):
    """Return full path of files in directory.

    Path may be a tuple of directories."""

    if type(directory) is tuple:
        for dirname in directory:
            for pathname in listdir(dirname):
                yield pathname
        return

    dirname = common.expanduser(directory)

    if not os.path.lexists(dirname):
        return

    for filename in os.listdir(dirname):
        yield os.path.join(dirname, filename)

def check_abspath_writable(path):
    if not os.access(path, os.W_OK):
        return False
        
    return True
    
def check_abspath_readable(path, recursive = False):
    if recursive and os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for item in dirs:
                item = os.path.join(root, item)
                
                if not os.access(item, os.R_OK):
                    return False, item
                    
            for item in files:
                item = os.path.join(root, item)
                
                if not os.access(item, os.R_OK):
                    return False, item
                    
        return True, ""
        
    if not os.access(path, os.R_OK):
        return False, path
        
    return True, ""
    
def check_file_exists(path):
    for i in path:
        if os.path.exists(i):
            return True
            
    return False

def get_directory_size(start_path = '.'):
    total_size = 0

    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
            
    return total_size

def cat(path, mode = "rb"):
    data = ""
    
    try:
        if os.path.exists(path):
            with open(path, mode) as fin:
                data = fin.read()
    except Exception as e:
        pass
        
    return data
    
def rm(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

        return ""
    except Exception as e:
        return to_ts(str(e))

def enum_file_path(path, result):
    if os.path.isdir(path):
        
        try:
            files = os.listdir(path)
            result.append(path)
        except Exception as e:
            files = []
            
        for file in files:
            abspath = os.sep.join([path, file])

            if os.path.isdir(abspath):
                enum_file_path(abspath, result)
            else:
                result.append(abspath)
    else:
        result.append(path)

def identifytype(path):
    mine = "Dir"

    if os.path.isfile(path):
        try:
            import magic
            mine = magic.from_file(path, mime = True)
            mine = mine if mine else "Unknown"
        except Exception as e:
            mine = "File"
            
    return mine

def mode_to_letter(mode):
    if stat.S_ISDIR(mode):
        return 'DIR'
    elif stat.S_ISBLK(mode):
        return 'BLK'
    elif stat.S_ISCHR(mode):
        return 'CHR'
    elif stat.S_ISFIFO(mode):
        return 'FIFO'
    elif stat.S_ISSOCK(mode):
        return 'SOCK'
    elif stat.S_ISLNK(mode):
        return 'LNK'
    else:
        return ''

def delete_locked_file(pathname):
    """Delete a file that is currently in use"""
    if common.is_windows():
        from ctypes import windll, c_ulong, c_buffer, byref, sizeof

        if os.path.exists(pathname):
            MOVEFILE_DELAY_UNTIL_REBOOT = 4
            if 0 == windll.kernel32.MoveFileExW(pathname, None, MOVEFILE_DELAY_UNTIL_REBOOT):
                from ctypes import WinError
                raise WinError()

def delete(path, shred = False, ignore_missing = False, allow_shred = True):
    """Delete path that is either file, directory, link or FIFO.

       If shred is enabled as a function parameter or the BleachBit global
       parameter, the path will be shredded unless allow_shred = False.
    """
    is_special = False
    path = extended_path(path)

    if not os.path.lexists(path):
        if ignore_missing:
            return

        raise OSError(2, 'No such file or directory', path)

    if 'posix' == os.name:
        # With certain (relatively rare) files on Windows os.lstat()
        # may return Access Denied
        mode = os.lstat(path)[stat.ST_MODE]
        is_special = stat.S_ISFIFO(mode) or stat.S_ISLNK(mode)

    if is_special:
        os.remove(path)
    elif os.path.isdir(path):
        delpath = path

        if allow_shred and shred:
            delpath = wipe_name(path)

        shutil.rmtree(delpath)

    elif os.path.isfile(path):
        # wipe contents
        if allow_shred and shred:
            try:
                wipe_contents(path)
            except pywinerror as e:
                # 2 = The system cannot find the file specified.
                # This can happen with a broken symlink
                # https://github.com/bleachbit/bleachbit/issues/195
                if 2 != e.winerror:
                    raise
                # If a broken symlink, try os.remove() below.
            except IOError as e:
                # permission denied (13) happens shredding MSIE 8 on Windows 7
                print(__name__, "IOError #%s shredding '%s'", e.errno, path)
            # wipe name
            os.remove(wipe_name(path))
        else:
            # unlink
            os.remove(path)
    else:
        raise "special file type cannot be deleted: {}".format(path)
        
def children_in_directory(top, list_directories=False):
    """Iterate files and, optionally, subdirectories in directory"""
    if type(top) is tuple:
        for top_ in top:
            for pathname in children_in_directory(top_, list_directories):
                yield pathname
        return

    for (dirpath, dirnames, filenames) in os.walk(top, topdown=False):
        if list_directories:
            for dirname in dirnames:
                yield os.path.join(dirpath, dirname)

        for filename in filenames:
            yield os.path.join(dirpath, filename)
            
def getsize(path):
    """Return the actual file size considering spare files
       and symlinks"""
    if 'posix' == os.name:
        try:
            __stat = os.lstat(path)
        except OSError as e:
            # OSError: [Errno 13] Permission denied
            # can happen when a regular user is trying to find the size of /var/log/hp/tmp
            # where /var/log/hp is 0774 and /var/log/hp/tmp is 1774
            if errno.EACCES == e.errno:
                return 0
            raise
        return __stat.st_blocks * 512

    if 'nt' == os.name:
        import win32file
        # On rare files os.path.getsize() returns access denied, so first
        # try FindFilesW.
        # Also, apply prefix to use extended-length paths to support longer
        # filenames.
        finddata = win32file.FindFilesW(extended_path(path))
        if not finddata:
            # FindFilesW does not work for directories, so fall back to
            # getsize()
            return os.path.getsize(path)
        else:
            size = (finddata[0][4] * (0xffffffff + 1)) + finddata[0][5]
            return size

    return os.path.getsize(path)

def getsizedir(path):
    """Return the size of the contents of a directory"""
    total_bytes = 0
    for node in children_in_directory(path, list_directories=False):
        total_bytes += getsize(node)
    return total_bytes

def clean_json(path, target):
    """Delete key in the JSON file"""
    import json
    changed = False
    targets = target.split('/')

    # read file to parser
    js = json.load(open(path, 'r'))

    # change file
    pos = js
    while True:
        new_target = targets.pop(0)
        if not isinstance(pos, dict):
            break
        if new_target in pos and len(targets) > 0:
            # descend
            pos = pos[new_target]
        elif new_target in pos:
            # delete terminal target
            changed = True
            del(pos[new_target])
        else:
            # target not found
            break
        if 0 == len(targets):
            # target not found
            break

    if changed:
        from bleachbit.Options import options
        if options.get('shred'):
            delete(path, True)
        # write file
        json.dump(js, open(path, 'w'))

def clean_ini(path, section, parameter):
    """Delete sections and parameters (aka option) in the file"""

    # read file to parser
    config = bleachbit.RawConfigParser()
    fp = codecs.open(path, 'r', encoding='utf_8_sig')
    config.readfp(fp)

    # change file
    changed = False
    if config.has_section(section):
        if parameter is None:
            changed = True
            config.remove_section(section)
        elif config.has_option(section, parameter):
            changed = True
            config.remove_option(section, parameter)

    # write file
    if changed:
        from bleachbit.Options import options
        fp.close()
        if options.get('shred'):
            delete(path, True)
        fp = codecs.open(path, 'wb', encoding='utf_8')
        config.write(fp)

def extended_path(path):
    """If applicable, return the extended Windows pathname"""
    if 'nt' == os.name:
        if path.startswith(r'\\?'):
            return path
        if path.startswith(r'\\'):
            return '\\\\?\\unc\\' + path[2:]
        return '\\\\?\\' + path
    return path

def wipe_name(pathname1):
    """Wipe the original filename and return the new pathname"""
    (head, _) = os.path.split(pathname1)
    # reference http://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
    maxlen = 226
    # first, rename to a long name
    i = 0
    while True:
        try:
            pathname2 = os.path.join(head, __random_string(maxlen))
            os.rename(pathname1,  pathname2)
            break
        except OSError:
            if maxlen > 10:
                maxlen -= 10
            i += 1
            if i > 100:
                print('exhausted long rename: %s', pathname1)
                pathname2 = pathname1
                break
    # finally, rename to a short name
    i = 0
    while True:
        try:
            pathname3 = os.path.join(head, __random_string(i + 1))
            os.rename(pathname2, pathname3)
            break
        except:
            i += 1
            if i > 100:
                print('exhausted short rename: %s', pathname2)
                pathname3 = pathname2
                break
    return pathname3

def wipe_contents(path, truncate=True):
    """Wipe files contents

    http://en.wikipedia.org/wiki/Data_remanence
    2006 NIST Special Publication 800-88 (p. 7): "Studies have
    shown that most of today's media can be effectively cleared
    by one overwrite"
    """

    def wipe_write():
        size = getsize(path)
        try:
            f = open(path, 'wb')
        except IOError as e:
            if e.errno == errno.EACCES:  # permission denied
                os.chmod(path, 0o200)  # user write only
                f = open(path, 'wb')
            else:
                raise
        blanks = chr(0) * 4096
        while size > 0:
            f.write(blanks)
            size -= 4096
        f.flush()  # flush to OS buffer
        os.fsync(f.fileno())  # force write to disk
        return f

    if 'nt' == os.name:
        from win32com.shell.shell import IsUserAnAdmin

    if 'nt' == os.name and IsUserAnAdmin():
        from bleachbit.WindowsWipe import file_wipe, UnsupportedFileSystemError
        import warnings
        from bleachbit import _
        try:
            file_wipe(path)
        except pywinerror as e:
            # 32=The process cannot access the file because it is being used by another process.
            # 33=The process cannot access the file because another process has
            # locked a portion of the file.
            if not e.winerror in (32, 33):
                # handle only locking errors
                raise
            # Try to truncate the file. This makes the behavior consistent
            # with Linux and with Windows when IsUserAdmin=False.
            try:
                with open(path, 'wb') as f:
                    truncate_f(f)
            except IOError as e2:
                if errno.EACCES == e2.errno:
                    # Common when the file is locked
                    # Errno 13 Permission Denied
                    pass
            # translate exception to mark file to deletion in Command.py
            raise WindowsError(e.winerror, e.strerror)
        except UnsupportedFileSystemError as e:
            warnings.warn(
                _('There was at least one file on a file system that does not support advanced overwriting.'), UserWarning)
            f = open(path, 'wb')
        else:
            # The wipe succeed, so prepare to truncate.
            f = open(path, 'wb')
    else:
        f = wipe_write()
    if truncate:
        truncate_f(f)
    f.close()


def wipe_name(pathname1):
    """Wipe the original filename and return the new pathname"""
    (head, _) = os.path.split(pathname1)
    # reference http://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
    maxlen = 226
    # first, rename to a long name
    i = 0
    while True:
        try:
            pathname2 = os.path.join(head, __random_string(maxlen))
            os.rename(pathname1,  pathname2)
            break
        except OSError:
            if maxlen > 10:
                maxlen -= 10
            i += 1
            if i > 100:
                print('exhausted long rename: %s', pathname1)
                pathname2 = pathname1
                break
    # finally, rename to a short name
    i = 0
    while True:
        try:
            pathname3 = os.path.join(head, __random_string(i + 1))
            os.rename(pathname2, pathname3)
            break
        except:
            i += 1
            if i > 100:
                print('exhausted short rename: %s', pathname2)
                pathname3 = pathname2
                break
    return pathname3


def wipe_path(pathname, idle=False):
    """Wipe the free space in the path
    This function uses an iterator to update the GUI."""

    def temporaryfile():
        # reference
        # http://en.wikipedia.org/wiki/Comparison_of_file_systems#Limits
        maxlen = 245
        f = None
        while True:
            try:
                f = tempfile.NamedTemporaryFile(
                    dir=pathname, suffix=__random_string(maxlen), delete=False)
                # In case the application closes prematurely, make sure this
                # file is deleted
                atexit.register(
                    delete, f.name, allow_shred=False, ignore_missing=True)
                break
            except OSError as e:
                if e.errno in (errno.ENAMETOOLONG, errno.ENOSPC, errno.ENOENT):
                    # ext3 on Linux 3.5 returns ENOSPC if the full path is greater than 264.
                    # Shrinking the size helps.

                    # Microsoft Windows returns ENOENT "No such file or directory"
                    # when the path is too long such as %TEMP% but not in C:\
                    if maxlen > 5:
                        maxlen -= 5
                        continue
                raise
        return f

    def estimate_completion():
        """Return (percent, seconds) to complete"""
        remaining_bytes = free_space(pathname)
        done_bytes = start_free_bytes - remaining_bytes
        if done_bytes < 0:
            # maybe user deleted large file after starting wipe
            done_bytes = 0
        if 0 == start_free_bytes:
            done_percent = 0
        else:
            done_percent = 1.0 * done_bytes / (start_free_bytes + 1)
        done_time = time.time() - start_time
        rate = done_bytes / (done_time + 0.0001)  # bytes per second
        remaining_seconds = int(remaining_bytes / (rate + 0.0001))
        return 1, done_percent, remaining_seconds

    print("wipe_path('%s')", pathname)
    files = []
    total_bytes = 0
    start_free_bytes = free_space(pathname)
    start_time = time.time()
    # Because FAT32 has a maximum file size of 4,294,967,295 bytes,
    # this loop is sometimes necessary to create multiple files.
    while True:
        try:
            print('creating new, temporary file to wipe path')
            f = temporaryfile()
        except OSError as e:
            # Linux gives errno 24
            # Windows gives errno 28 No space left on device
            if e.errno in (errno.EMFILE, errno.ENOSPC):
                break
            else:
                raise
        last_idle = time.time()
        # Write large blocks to quickly fill the disk.
        blanks = chr(0) * 65535
        while True:
            try:
                f.write(blanks)
            except IOError as e:
                if e.errno == errno.ENOSPC:
                    if len(blanks) > 1:
                        # Try writing smaller blocks
                        blanks = blanks[0: (len(blanks) / 2)]
                    else:
                        break
                elif e.errno != errno.EFBIG:
                    raise
            if idle and (time.time() - last_idle) > 2:
                # Keep the GUI responding, and allow the user to abort.
                # Also display the ETA.
                yield estimate_completion()
                last_idle = time.time()
        # Write to OS buffer
        try:
            f.flush()
        except:
            # IOError: [Errno 28] No space left on device
            # seen on Microsoft Windows XP SP3 with ~30GB free space but
            # not on another XP SP3 with 64MB free space
            print("info: exception on f.flush()")
        os.fsync(f.fileno())  # write to disk
        # Remember to delete
        files.append(f)
        # For statistics
        total_bytes += f.tell()
        # If no bytes were written, then quit
        if f.tell() < 1:
            break
    # sync to disk
    sync()
    # statistics
    elapsed_sec = time.time() - start_time
    rate_mbs = (total_bytes / (1000 * 1000)) / elapsed_sec
    print('wrote %d files and %d bytes in %d seconds at %.2f MB/s',
                len(files), total_bytes, elapsed_sec, rate_mbs)
    # how much free space is left (should be near zero)
    if 'posix' == os.name:
        stats = os.statvfs(pathname)
        print('%d bytes and %d inodes available to non-super-user',
                    stats.f_bsize * stats.f_bavail, stats.f_favail)
        print('%d bytes and %d inodes available to super-user',
                    stats.f_bsize * stats.f_bfree, stats.f_ffree)
    # truncate and close files
    for f in files:
        truncate_f(f)

        while True:
            try:
                # Nikita: I noticed a bug that prevented file handles from
                # being closed on FAT32. It sometimes takes two .close() calls
                # to do actually close (and therefore delete) a temporary file
                f.close()
                break
            except IOError as e:
                if e.errno == 0:
                    print('handled unknown error 0')
                    time.sleep(0.1)
        # explicitly delete
        delete(f.name, ignore_missing=True)
