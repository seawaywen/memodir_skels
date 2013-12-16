import subprocess
import sys
import platform
import shutil
import logging
import time
import os
from os.path import dirname, join, abspath
from optparse import OptionParser


###########################
# This variable is important
PROJECT_NAME = 'ATRR'
########################

PROJECT_VERSION = '3.0STD0'

###########################
# DEBUG mode or not
IS_PROD = True
###########################


if type('') is not type(b''):
    def u(s):
        return s
    bytes_type = bytes
    unicode_type = str
    basestring_type = str
else:
    def u(s):
        return s.decode('unicode_escape')
    bytes_type = str
    unicode_type = unicode
    basestring_type = basestring

_TO_UNICODE_TYPES = (unicode_type, type(None))


def to_unicode(value):
    """Converts a string argument to a unicode string.

    If the argument is already a unicode string or None, it is returned
    unchanged.  Otherwise it must be a byte string and is decoded as utf8.
    """
    if isinstance(value, _TO_UNICODE_TYPES):
        return value
    assert isinstance(value, bytes_type), \
        "Expected bytes, unicode, or None; got %r" % type(value)
    return value.decode("utf-8")

# to_unicode was previously named _unicode not because it was private,
# but to avoid conflicts with the built-in unicode() function/type
_unicode = to_unicode

try:
    import curses
except ImportError:
    curses = None


def _stderr_supports_color():
    color = False
    if curses and sys.stderr.isatty():
        try:
            curses.setupterm()
            if curses.tigetnum("colors") > 0:
                color = True
        except Exception:
            pass
    return color


class LogFormatter(logging.Formatter):
    """Log formatter used in Tornado.

    Key features of this formatter are:

    * Color support when logging to a terminal that supports it.
    * Timestamps on every log line.
    * Robust against str/bytes encoding problems.

    This formatter is enabled automatically by
    `tornado.options.parse_command_line` (unless ``--logging=none`` is
    used).
    """
    def __init__(self, color=True, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        self._color = color and _stderr_supports_color()
        if self._color:
            fg_color = (curses.tigetstr("setaf") or
                        curses.tigetstr("setf") or "")
            if (3, 0) < sys.version_info < (3, 2, 3):
                fg_color = unicode_type(fg_color, "ascii")
            self._colors = {
                logging.DEBUG: unicode_type(curses.tparm(fg_color, 4),  # Blue
                                            "ascii"),
                logging.INFO: unicode_type(curses.tparm(fg_color, 2),  # Green
                                           "ascii"),
                logging.WARNING: unicode_type(curses.tparm(fg_color, 3),  # Yellow
                                              "ascii"),
                logging.ERROR: unicode_type(curses.tparm(fg_color, 1),  # Red
                                            "ascii"),
            }
            self._normal = unicode_type(curses.tigetstr("sgr0"), "ascii")

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)
        assert isinstance(record.message, basestring_type)  # guaranteed by logging

        prefix = ''

        def safe_unicode(s):
            try:
                return _unicode(s)
            except UnicodeDecodeError:
                return repr(s)

        if self._color:
            formatted = prefix + self._colors.get(record.levelno, self._normal) + safe_unicode(record.message)
        else:
            formatted = prefix + safe_unicode(record.message)

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:

            lines = [formatted.rstrip()]
            lines.extend(safe_unicode(ln) for ln in record.exc_text.split('\n'))
            formatted = '\n'.join(lines)
        return formatted.replace("\n", "\n    ")

############################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO if IS_PROD else logging.DEBUG)
channel = logging.StreamHandler()
channel.setFormatter(LogFormatter())
logger.addHandler(channel)

ROOT_DIR = dirname(os.path.abspath(__file__))
BUILDOUT_DIR = join(ROOT_DIR, 'buildout')
BUILDOUT_BIN_DIR = join(BUILDOUT_DIR, 'bin')

if sys.platform == 'win32':
    BUILDOUT_CMD = join(BUILDOUT_BIN_DIR, 'buildout-script.py')
else:
    BUILDOUT_CMD = join(BUILDOUT_BIN_DIR, 'buildout')
BUILDOUT_CFG = join(BUILDOUT_DIR, 'buildout.cfg')
BUILDOUT_PROD_CFG = join(BUILDOUT_DIR, 'for_release.cfg')
DOWNLOAD_DIR = join(BUILDOUT_DIR, join('downloads' if IS_PROD else 'downloads_dev', 'dist'))

_interpreter = 'python{0}'.format('_dev' if os.path.exists(join(BUILDOUT_BIN_DIR, 'python_dev')) else '')
python_interpreter = '{0}{1}'.format(_interpreter, '-script.py' if sys.platform == 'win32' else '')
buildout_python = join(BUILDOUT_BIN_DIR, python_interpreter)


def is_bitnami_env():
    return sys.executable.endswith('.python.bin')


def get_executable_python():
    import sys

    if is_bitnami_env():
        executable_python = 'python'
    else:
        executable_python = sys.executable

    return executable_python


def splitter(split):
    logger.info(split * 60)


def print_error():
    logger.error(",------.,------. ,------.  ,-----. ,------.")
    logger.error("|  .---'|  .--. '|  .--. ''  .-.  '|  .--. '")
    logger.error("|  `--, |  '--'.'|  '--'.'|  | |  ||  '--'.'")
    logger.error("|  `---.|  |\  \ |  |\  \ '  '-'  '|  |\  \ ")
    logger.error("`------'`--' '--'`--' '--' `-----' `--' '--'")


def print_project_name():
    #http://patorjk.com/software/taag/#p=display&f=Soft&t=ATRR
    logger.warn("  ,---. ,--------.,------. ,------.")
    logger.warn(" /  O  \\'--.  .--'|  .--. '|  .--. '")
    logger.warn("|  .-.  |  |  |   |  '--'.'|  '--'.'")
    logger.warn("|  | |  |  |  |   |  |\  \ |  |\  \\")
    logger.warn("`--' `--'  `--'   `--' '--'`--' '--'")


#  1. if < 0.7, uninstall the old version
#  2. install the latest version
#  python ez_setup.py  --download-base=setuptools-1.1.6.tar.gz --user
def _check_setuptools_version():
    splitter('-')
    logger.info('[CHECKING Setuptools]')
    splitter('-')

    msg = 'Dependent Setuptools version for {1} installation. [{0}]'

    try:
        import setuptools
        version = setuptools.__version__
        if version < '0.7':
            _install_setuptools()
        else:
            logger.info(msg.format('OK', PROJECT_NAME))
    except ImportError:
        logger.error(msg.format('failed', PROJECT_NAME))

        logger.error('Setuptools is not installed')
        logger.info('Prepare install setuptools...')
        _install_setuptools()

    logger.info(' ')


def _install_setuptools():
    #import site; site.getsitepackages()
    #['/usr/local/lib/python2.7/dist-packages', '/usr/lib/python2.7/dist-packages']

    #setuptools_package = join(ROOT_DIR, join('utils', 'setuptools-1.1.6.tar.gz'))
    util_dir = join(ROOT_DIR, 'utils')

    command = r"cd utils " \
              " && " \
              "{0} {1} " \
              "--download-base={2}".format(get_executable_python(),
                                           join(util_dir, 'ez_setup.py'),
                                           util_dir + os.sep)
    if sys.platform in ['linux2', 'darwin']:
        # if python is in VirtualEnv, ignore the user level
        if not hasattr(sys, 'real_prefix'):
            command += ' --user'

    logger.debug('[command]{0}'.format(command))

    subprocess.check_call(command, shell=True)


def _check_command(cmd):
    if sys.platform in ['linux2', 'darwin']:
        splitter('-')
        logger.info('[CHECKING {0}]'.format(cmd))
        splitter('-')

        msg = 'Dependent {1} for {2} installation. [{0}]'

        command = ['which', cmd]
        try:
            result = subprocess.call(command)
        except subprocess.CalledProcessError:
            result = -1

        if result == 0:
            logger.info(msg.format('OK', cmd, PROJECT_NAME))
        else:
            logger.error(msg.format('failed', cmd, PROJECT_NAME))
            print_error()
            logger.info('Install {0} as prerequisite first.'.format(cmd))
            exit(0)

        logger.info(' ')


def _check_make():
    _check_command('make')


def _check_gcc():
    _check_command('gcc')


def _check_g2plus():
    _check_command('g++')


def _check_space_in_cur_dir():
    #todo: Support the path with space in next version
    cur_dir = dirname(abspath(__file__))
    if cur_dir.find(' ') > 0:
        print_error()
        logger.error('Please make sure {0}\'s root path does NOT have SPACE'.format(PROJECT_NAME))
        exit(0)


def check_prerequisites():
    splitter('=')
    logger.info('[CHECKING PREREQUISITIONS]')
    splitter('=')

    _check_make()
    _check_gcc()
    _check_g2plus()
    _check_setuptools_version()

    _check_space_in_cur_dir()

    #todo: check if mysql existed on Posix compatible platform
    # check /usr/bin/mysql_config existed
    #todo: Package the Mysql-python lib with distribute
    #todo: test installing the reportlab without network connection

    logger.info(' ')


def is_python_version_valid():
    min_version = '2.6.5'
    version = sys.version
    if version < min_version:
        splitter('-')
        print_error()
        logger.error('####### ERROR: PYTHON VERSION IS TOO LOW #########')
        logger.error('Python version is too low, please use >%s version' % min_version)
        logger.error('Quit.')
        return False
    return True


def check_admin_right():
    """
    :check_Permissions
    echo Administrative permissions required. Detecting permissions...

    net session >nul 2>&1
    if %errorLevel% == 0 (
        echo Success: Administrative permissions confirmed.
    ) else (
        echo Failure: Current permissions inadequate.
    )

    pause >nul
    """

    if sys.platform == 'win32':
        msg = 'The Admin Permission. [{0}]'

        check_script = join(ROOT_DIR, join('utils', 'check_Permissions.bat'))
        #logger.debug(check_script)
        splitter('=')
        logger.info('[CHECKING ADMIN PERMISSION]')
        splitter('=')
        rtn_code = subprocess.check_output(check_script)
        #logger.error(rtn_code)
        if rtn_code is not None and rtn_code[0] == '0':
            logger.info(msg.format('OK'))
            logger.info('\n')
        else:
            logger.error(msg.format('failed'))

            print_error()
            logger.error('####### ERROR: ADMINISTRATOR PRIVILEGES REQUIRED #########')
            logger.error('Please open command terminal with Administrative permission!!!')
            logger.error('\n')
            exit(0)


def platform_validation():
    info_list = platform.uname()
    logger.info('[PLATFORM] {0}'.format(info_list[0]))
    logger.info(' ')


def wait_for_required_bin(app_name):
    #build_out_path = os.path.join(BUILDOUT_BIN_DIR, appName)
    while True:
        if os.path.exists(app_name):
            break
        else:
            time.sleep(5)


def run_buildout(task=None):
    splitter('=')
    logger.info("[BUILDOUT RUNNING]")
    splitter('=')

    wait_for_required_bin(BUILDOUT_CMD)

    buildout_cfg_file = BUILDOUT_PROD_CFG if IS_PROD else BUILDOUT_CFG

    command = [get_executable_python(), BUILDOUT_CMD, ]

    if task is None:
        command.extend(['-c',
                        buildout_cfg_file])
    else:
        command.extend(['install', task,
                        '-c', buildout_cfg_file])

    subprocess.call(command, shell=True if sys.platform == 'win32' else False)

    logger.info('[command] {0}'.format(' '.join(command)))

    logger.info('\n')


def setup_buildout_env():
    splitter('=')
    logger.info('[BOOTSTRAP RUNNING]')
    splitter('=')

    logger.info('Setup the BUILDOUT environment...')
    logger.info(' ')

    _download_dir = 'downloads' if IS_PROD else 'downloads_dev'
    if not os.path.exists(DOWNLOAD_DIR):
        logger.info('{0} folder not existed, create new one...'.format(_download_dir))
        os.makedirs(DOWNLOAD_DIR)

        logger.debug('Copying the zc.buildout package to download folder to setup env.')
        zc_buildout_name = 'zc.buildout-2.2.1.tar.gz'
        zc_buildout_package = join(ROOT_DIR, join('utils', zc_buildout_name))
        shutil.copy(zc_buildout_package, join(DOWNLOAD_DIR, zc_buildout_name))

    buildout_conf_file = BUILDOUT_PROD_CFG if IS_PROD else BUILDOUT_CFG
    command = [
        get_executable_python(),
        join(BUILDOUT_DIR, 'bootstrap.py'),
        '-c', buildout_conf_file,
        '-f', DOWNLOAD_DIR,
        '-v', '2.2.1',
    ]

    logger.debug('[command]'+' '.join(command))
    subprocess.call(command)

    logger.debug('\n')


def gen_key_by_proj_name(key, _project_name=None):
    if key is None or key == '':
        raise ValueError("{0} can't be None or empty")

    if _project_name is None:
        project_name = os.environ['QT_PROJ_NAME']
    else:
        project_name = _project_name

    return '{0}_{1}'.format(project_name, key.upper())


def set_env_vars():
    os.environ['QT_PROJ_NAME'] = PROJECT_NAME
    os.environ[gen_key_by_proj_name('HOME')] = dirname(abspath(__file__))
    os.environ[gen_key_by_proj_name('IS_PROD')] = str(IS_PROD)


def create_buildout_env():
    if os.path.exists(buildout_python):
        subprocess.call([get_executable_python(),
                         buildout_python,
                         'deploy.py',
                         '-k'],
                        shell=True if sys.platform == 'win32' else False)

    if sys.platform == 'win32':
        subprocess.call(['cls'], shell=True)
    else:
        subprocess.call('clear')

    splitter('*')
    splitter('*')

    print_project_name()
    logger.warn(' ' * 32 + '{0} [{1}] INSTALLATION {2} '.format(PROJECT_NAME,
                                                                PROJECT_VERSION,
                                                                '(dev mode)' if not IS_PROD else ''))

    splitter('*')
    splitter('*')

    time.sleep(3)

    logger.debug(' ')

    platform_validation()

    #check_admin_right()

    if is_python_version_valid():

        check_prerequisites()

        setup_buildout_env()

        run_buildout()

        logger.info('\n')

    else:
        exit(0)


def run_deploy():

    if os.path.exists(buildout_python):
        subprocess.call([get_executable_python(), buildout_python, 'deploy.py'],
                        shell=True if sys.platform == 'win32' else False)
    else:
        logger.info('\n')
        splitter('*')
        print_error()
        logger.info('Product running environment building failed.')
        splitter('*')

    logger.info('\n')


if __name__ == '__main__':
    usage = '''\
    [DESIRED PYTHON FOR APPLICATION] deploy.py [options]

    Bootstraps {0} django application.

    Simply run this script in a directory containing a buildout.cfg, using the
    Python that you want bin/buildout to use.

    '''.format(PROJECT_NAME)

    parser = OptionParser(usage=usage)

    parser.add_option("-b", "--build_env",
                      dest="build_env",
                      action="store_true",
                      default=False,
                      help="Setup buildout environment")

    parser.add_option("-i", "--init",
                      dest="init",
                      action="store_true",
                      default=False,
                      help="Init buildout settings")

    parser.add_option("-s", "--start",
                      dest="start",
                      action="store_true",
                      default=False,
                      help="Start app server(s)")

    parser.add_option("-e", "--restart",
                      dest="restart",
                      action="store_true",
                      default=False,
                      help="Restart app and web server(s)")

    parser.add_option("-k", "--stop",
                      dest="stop",
                      action="store_true",
                      default=False,
                      help="Stop host server")

    parser.add_option("-a", "--stop-all",
                      dest="stop_all",
                      action="store_true",
                      default=False,
                      help="Stop all servers")

    parser.add_option("-u", "--upgrade",
                      dest="upgrade",
                      action="store_true",
                      default=False,
                      help="Upgrade")

    options, args = parser.parse_args()

    set_env_vars()

    if options.build_env is not None and options.build_env:
        create_buildout_env()

    elif options.init is not None and options.init:

        create_buildout_env()
        run_deploy()

    else:

        from qt.deploy.deploy import Deploy

        deploy = Deploy()

        if options.upgrade is not None and options.upgrade:
            deploy.upgrade()

        if options.start is not None and options.start:
            deploy.splitter()
            deploy.start_default_app_server()

            #deploy.splitter()
            #deploy.start_all_user_app_servers()

            deploy.splitter()
            deploy.start_nginx_server()

            deploy.splitter()

        elif options.restart is not None and options.restart:
            #deploy.splitter()
            #deploy.kill_all_app_servers()

            deploy.splitter()
            deploy.kill_all_app_servers()

            deploy.splitter()
            deploy.stop_default_app_server()
            deploy.start_default_app_server()

            #deploy.splitter()
            #deploy.start_all_user_app_servers()

            deploy.splitter()
            deploy.restart_nginx_server()

            deploy.splitter()
            host_name, port, ip = (deploy.helper.get_host_name(),
                                   deploy.get_web_server_port(),
                                   deploy.helper.get_host_ip())
            logger.info('\n')
            deploy.splitter('*')
            deploy.splitter('-')
            logger.info("Service is up now")
            deploy.splitter('-')
            logger.info(' ')
            logger.info("- Open one of following address in browser to visit the application.")
            logger.info('  http://%s:%s' % (host_name, port))
            logger.info('  http://%s:%s' % (deploy.helper.get_host_ip(), deploy.get_web_server_port()))
            logger.info(' ')
            deploy.splitter('*')

        elif options.stop is not None and options.stop:
            deploy.splitter()
            deploy.kill_all_app_servers()
            deploy.stop_default_app_server()

            deploy.splitter()
            deploy.stop_nginx_server()

            deploy.splitter()

        elif options.stop_all is not None and options.stop_all:
            deploy.splitter()
            deploy.kill_all_app_servers()
            deploy.stop_default_app_server()
            deploy.kill_all_app_servers()

            deploy.splitter()
            deploy.stop_nginx_server()

            deploy.splitter()
        else:
            deploy.deploy()

        #try:
        #except Exception:
        #    raise ImportError('qt.deploy.deploy not existed')
