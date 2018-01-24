from utils import file_op
import glob
import logging
import os
import re
import sys
import subprocess

if 'win32' == sys.platform:
    import _winreg
    import pywintypes
    import win32api
    import win32con
    import win32file
    import win32gui
    import win32process

    from ctypes import windll, c_ulong, c_buffer, byref, sizeof
    from win32com.shell import shell, shellcon

    psapi = windll.psapi
    kernel = windll.kernel32

def yum_clean():
    """Run 'yum clean all' and return size in bytes recovered"""
    if os.path.exists('/var/run/yum.pid'):
        msg = _(
            "%s cannot be cleaned because it is currently running.  Close it, and try again.") % "Yum"
        raise RuntimeError(msg)

    old_size = file_op.getsizedir('/var/cache/yum')
    args = ['--enablerepo=*', 'clean', 'all']
    invalid = ['You need to be root', 'Cannot remove rpmdb file']
    run_cleaner_cmd('yum', args, '^unused regex$', invalid)
    new_size = file_op.getsizedir('/var/cache/yum')
    return old_size - new_size

def run_cleaner_cmd(cmd, args, freed_space_regex=r'[\d.]+[kMGTE]?B?', error_line_regexes=None):
    """Runs a specified command and returns how much space was (reportedly) freed.
    The subprocess shouldn't need any user input and the user should have the
    necessary rights.
    freed_space_regex gets applied to every output line, if the re matches,
    add values captured by the single group in the regex"""
    if not file_op.exe_exists(cmd):
        raise RuntimeError(_('Executable not found: %s') % cmd)
    freed_space_regex = re.compile(freed_space_regex)
    error_line_regexes = [re.compile(regex) for regex in error_line_regexes or []]

    env = {'LC_ALL': 'C', 'PATH': os.getenv('PATH')}
    output = subprocess.check_output([cmd] + args, stderr=subprocess.STDOUT,
                                     universal_newlines=True, env=env)
    freed_space = 0
    for line in output.split('\n'):
        m = freed_space_regex.match(line)
        if m is not None:
            freed_space += file_op.human_to_bytes(m.group(1))
        for error_re in error_line_regexes:
            if error_re.search(line):
                raise RuntimeError('Invalid output from %s: %s' % (cmd, line))

    return freed_space

def shell_change_notify():
    """Notify the Windows shell of update.

    Used in windows_explorer.xml."""
    shell.SHChangeNotify(shellcon.SHCNE_ASSOCCHANGED, shellcon.SHCNF_IDLIST,
                         None, None)
    return 0

def vacuum_sqlite3(path):
    """Vacuum SQLite database"""
    execute_sqlite3(path, 'vacuum')

def execute_sqlite3(path, cmds):
    """Execute 'cmds' on SQLite database 'path'"""
    import sqlite3
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # overwrites deleted content with zeros
    # https://www.sqlite.org/pragma.html#pragma_secure_delete
    from bleachbit.Options import options
    if options.get('shred'):
        cursor.execute('PRAGMA secure_delete=ON')

    for cmd in cmds.split(';'):
        try:
            cursor.execute(cmd)
        except sqlite3.DatabaseError as exc:
            raise sqlite3.DatabaseError(
                '%s: %s' % (bleachbit.decode_str(exc), path))
        except sqlite3.OperationalError as exc:
            if exc.message.find('no such function: ') >= 0:
                # fixme: determine why randomblob and zeroblob are not
                # available
                logger.exception(exc.message)
            else:
                raise sqlite3.OperationalError(
                    '%s: %s' % (bleachbit.decode_str(exc), path))
    cursor.close()
    conn.commit()
    conn.close()

def delete_office_registrymodifications(path):
    """Erase LibreOffice 3.4 and Apache OpenOffice.org 3.4 MRU in registrymodifications.xcu"""
    import xml.dom.minidom
    dom1 = xml.dom.minidom.parse(path)
    modified = False
    for node in dom1.getElementsByTagName("item"):
        if not node.hasAttribute("oor:path"):
            continue
        if not node.getAttribute("oor:path").startswith('/org.openoffice.Office.Histories/Histories/'):
            continue
        node.parentNode.removeChild(node)
        node.unlink()
        modified = True
    if modified:
        dom1.writexml(open(path, "w"))

def delete_mozilla_url_history(path):
    """Delete URL history in Mozilla places.sqlite (Firefox 3 and family)"""

    cmds = ""

    # delete the URLs in moz_places
    places_suffix = "where id in (select " \
        "moz_places.id from moz_places " \
        "left join moz_bookmarks on moz_bookmarks.fk = moz_places.id " \
        "where moz_bookmarks.id is null); "

    cols = ('url', 'rev_host', 'title')
    cmds += __shred_sqlite_char_columns('moz_places', cols, places_suffix)

    # delete any orphaned annotations in moz_annos
    annos_suffix = "where id in (select moz_annos.id " \
        "from moz_annos " \
        "left join moz_places " \
        "on moz_annos.place_id = moz_places.id " \
        "where moz_places.id is null); "

    cmds += __shred_sqlite_char_columns(
        'moz_annos', ('content', ), annos_suffix)

    # delete any orphaned favicons
    fav_suffix = "where id not in (select favicon_id " \
        "from moz_places where favicon_id is not null ); "

    if __sqlite_table_exists(path, 'moz_favicons'):
        cols = ('url', 'data')
        cmds += __shred_sqlite_char_columns('moz_favicons', cols, fav_suffix)

    # delete any orphaned history visits
    cmds += "delete from moz_historyvisits where place_id not " \
        "in (select id from moz_places where id is not null); "

    # delete any orphaned input history
    input_suffix = "where place_id not in (select distinct id from moz_places)"
    cols = ('input', )
    cmds += __shred_sqlite_char_columns('moz_inputhistory', cols, input_suffix)

    # delete the whole moz_hosts table
    # Reference: https://bugzilla.mozilla.org/show_bug.cgi?id=932036
    # Reference:
    # https://support.mozilla.org/en-US/questions/937290#answer-400987
    if __sqlite_table_exists(path, 'moz_hosts'):
        cmds += __shred_sqlite_char_columns('moz_hosts', ('host',))
        cmds += "delete from moz_hosts;"

    # execute the commands
    file_op.execute_sqlite3(path, cmds)

def journald_clean():
    """Clean the system journals"""
    freed_space_regex = '^Vacuuming done, freed ([\d.]+[KMGT]?) of archived journals on disk.$'
    return run_cleaner_cmd('journalctl', ['--vacuum-size=1'], freed_space_regex)

def delete_chrome_keywords(path):
    """Delete keywords table in Chromium/Google Chrome 'Web Data' database"""
    cols = ('short_name', 'keyword', 'favicon_url',
            'originating_url', 'suggest_url')
    where = "where not date_created = 0"
    cmds = __shred_sqlite_char_columns('keywords', cols, where)
    cmds += "update keywords set usage_count = 0;"
    ver = __get_chrome_history(path, 'Web Data')
    if 43 <= ver < 49:
        # keywords_backup table first seen in Google Chrome 17 / Chromium 17 which is Web Data version 43
        # In Google Chrome 25, the table is gone.
        cmds += __shred_sqlite_char_columns('keywords_backup', cols, where)
        cmds += "update keywords_backup set usage_count = 0;"

    file_op.execute_sqlite3(path, cmds)

def delete_chrome_history(path):
    """Clean history from History and Favicon files without affecting bookmarks"""
    cols = ('url', 'title')
    where = ""
    ids_int = get_chrome_bookmark_ids(path)
    if ids_int:
        ids_str = ",".join([str(id0) for id0 in ids_int])
        where = "where id not in (%s) " % ids_str
    cmds = __shred_sqlite_char_columns('urls', cols, where)
    cmds += __shred_sqlite_char_columns('visits')
    cols = ('lower_term', 'term')
    cmds += __shred_sqlite_char_columns('keyword_search_terms', cols)
    ver = __get_chrome_history(path)
    if ver >= 20:
        # downloads, segments, segment_usage first seen in Chrome 14,
        #   Google Chrome 15 (database version = 20).
        # Google Chrome 30 (database version 28) doesn't have full_path, but it
        # does have current_path and target_path
        if ver >= 28:
            cmds += __shred_sqlite_char_columns(
                'downloads', ('current_path', 'target_path'))
            cmds += __shred_sqlite_char_columns(
                'downloads_url_chains', ('url', ))
        else:
            cmds += __shred_sqlite_char_columns(
                'downloads', ('full_path', 'url'))
        cmds += __shred_sqlite_char_columns('segments', ('name',))
        cmds += __shred_sqlite_char_columns('segment_usage')
    file_op.execute_sqlite3(path, cmds)

def get_chrome_bookmark_ids(history_path):
    """Given the path of a history file, return the ids in the
    urls table that are bookmarks"""
    bookmark_path = os.path.join(os.path.dirname(history_path), 'Bookmarks')
    if not os.path.exists(bookmark_path):
        return []
    urls = get_chrome_bookmark_urls(bookmark_path)
    ids = []
    for url in urls:
        ids += get_sqlite_int(
            history_path, 'select id from urls where url=?', (url,))
    return ids

def get_chrome_bookmark_urls(path):
    """Return a list of bookmarked URLs in Google Chrome/Chromium"""
    import json

    # read file to parser
    js = json.load(open(path, 'r'))

    # empty list
    urls = []

    # local recursive function
    def get_chrome_bookmark_urls_helper(node):
        if not isinstance(node, dict):
            return
        if 'type' not in node:
            return
        if node['type'] == "folder":
            # folders have children
            for child in node['children']:
                get_chrome_bookmark_urls_helper(child)
        if node['type'] == "url" and 'url' in node:
            urls.append(node['url'])

    # find bookmarks
    for node in js['roots']:
        get_chrome_bookmark_urls_helper(js['roots'][node])

    return list(set(urls))  # unique

def get_sqlite_int(path, sql, parameters=None):
    """Run SQL on database in 'path' and return the integers"""
    ids = []
    import sqlite3
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    if parameters:
        cursor.execute(sql, parameters)
    else:
        cursor.execute(sql)
    for row in cursor:
        ids.append(int(row[0]))
    cursor.close()
    conn.close()
    return ids

def __shred_sqlite_char_columns(table, cols=None, where=""):
    """Create an SQL command to shred character columns"""
    cmd = ""
    if cols and options.get('shred'):
        cmd += "update or ignore %s set %s %s;" % \
            (table, ",".join(["%s = randomblob(length(%s))" % (col, col)
                              for col in cols]), where)
        cmd += "update or ignore %s set %s %s;" % \
            (table, ",".join(["%s = zeroblob(length(%s))" % (col, col)
                              for col in cols]), where)
    cmd += "delete from %s %s;" % (table, where)
    return cmd

def __get_chrome_history(path, fn='History'):
    """Get Google Chrome or Chromium history version.  'path' is name of any file in same directory"""
    path_history = os.path.join(os.path.dirname(path), fn)
    ver = get_sqlite_int(
        path_history, 'select value from meta where key="version"')[0]
    assert ver > 1
    return ver

def delete_chrome_favicons(path):
    """Delete Google Chrome and Chromium favicons not use in in history for bookmarks"""

    path_history = os.path.join(os.path.dirname(path), 'History')
    ver = __get_chrome_history(path)
    cmds = ""

    if ver in (4, 20, 22, 23, 25, 26, 28, 29, 32, 36, 37):
        # Version 4 includes Chromium 12
        # Version 20 includes Chromium 14, Google Chrome 15, Google Chrome 19
        # Version 22 includes Google Chrome 20
        # Version 25 is Google Chrome 26
        # Version 26 is Google Chrome 29
        # Version 28 is Google Chrome 30
        # Version 29 is Google Chrome 37
        # Version 32 is Google Chrome 51
        # Version 36 is Google Chrome 60

        # icon_mapping
        cols = ('page_url',)
        where = None
        if os.path.exists(path_history):
            cmds += "attach database \"%s\" as History;" % path_history
            where = "where page_url not in (select distinct url from History.urls)"
        cmds += __shred_sqlite_char_columns('icon_mapping', cols, where)

        # favicon images
        cols = ('image_data', )
        where = "where icon_id not in (select distinct icon_id from icon_mapping)"
        cmds += __shred_sqlite_char_columns('favicon_bitmaps', cols, where)

        # favicons
        # Google Chrome 30 (database version 28): image_data moved to table
        # favicon_bitmaps
        if ver < 28:
            cols = ('url', 'image_data')
        else:
            cols = ('url', )
        where = "where id not in (select distinct icon_id from icon_mapping)"
        cmds += __shred_sqlite_char_columns('favicons', cols, where)
    elif 3 == ver:
        # Version 3 includes Google Chrome 11

        cols = ('url', 'image_data')
        where = None
        if os.path.exists(path_history):
            cmds += "attach database \"%s\" as History;" % path_history
            where = "where id not in(select distinct favicon_id from History.urls)"
        cmds += __shred_sqlite_char_columns('favicons', cols, where)
    else:
        raise RuntimeError('%s is version %d' % (path, ver))

    file_op.execute_sqlite3(path, cmds)

def delete_chrome_autofill(path):
    """Delete autofill table in Chromium/Google Chrome 'Web Data' database"""
    cols = ('name', 'value', 'value_lower')
    cmds = __shred_sqlite_char_columns('autofill', cols)
    cols = ('first_name', 'middle_name', 'last_name', 'full_name')
    cmds += __shred_sqlite_char_columns('autofill_profile_names', cols)
    cmds += __shred_sqlite_char_columns('autofill_profile_emails', ('email',))
    cmds += __shred_sqlite_char_columns('autofill_profile_phones', ('number',))
    cols = ('company_name', 'street_address', 'dependent_locality',
            'city', 'state', 'zipcode', 'country_code')
    cmds += __shred_sqlite_char_columns('autofill_profiles', cols)
    cols = (
        'company_name', 'street_address', 'address_1', 'address_2', 'address_3', 'address_4',
        'postal_code', 'country_code', 'language_code', 'recipient_name', 'phone_number')
    cmds += __shred_sqlite_char_columns('server_addresses', cols)
    file_op.execute_sqlite3(path, cmds)

def delete_chrome_databases_db(path):
    """Delete remote HTML5 cookies (avoiding extension data) from the Databases.db file"""
    cols = ('origin', 'name', 'description')
    where = "where origin not like 'chrome-%'"
    cmds = __shred_sqlite_char_columns('Databases', cols, where)
    file_op.execute_sqlite3(path, cmds)

def apt_autoremove():
    """Run 'apt-get autoremove' and return the size (un-rounded, in bytes) of freed space"""

    args = ['--yes', 'autoremove']
    # After this operation, 74.7MB disk space will be freed.
    freed_space_regex = r', ([\d.]+[a-zA-Z]{2}) disk space will be freed'
    try:
        return run_cleaner_cmd('apt-get', args, freed_space_regex, ['^E: '])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error calling '%s':\n%s" % (' '.join(e.cmd), e.output))

def apt_autoclean():
    """Run 'apt-get autoclean' and return the size (un-rounded, in bytes) of freed space"""
    try:
        return run_cleaner_cmd('apt-get', ['autoclean'], r'^Del .*\[([\d.]+[a-zA-Z]{2})}]', ['^E: '])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error calling '%s':\n%s" % (' '.join(e.cmd), e.output))

def apt_clean():
    """Run 'apt-get clean' and return the size in bytes of freed space"""
    old_size = get_apt_size()
    try:
        run_cleaner_cmd('apt-get', ['clean'], '^unused regex$', ['^E: '])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error calling '%s':\n%s" %
                           (' '.join(e.cmd), e.output))
    new_size = get_apt_size()
    return old_size - new_size

def get_apt_size():
    """Return the size of the apt cache (in bytes)"""
    data, success, retcode = common.exec_command(['apt-get', '-s', 'clean'])
    paths = re.findall('/[/a-z\.\*]+', data)
    return get_globs_size(paths)
    
def get_globs_size(paths):
    """Get the cumulative size (in bytes) of a list of globs"""
    total_size = 0
    
    for path in paths:
        from glob import iglob
        for p in iglob(path):
            total_size += file_op.getsize(p)

    return total_size