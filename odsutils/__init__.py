from os.path import join
from importlib.metadata import version
__version__ = version('odsutils')

try:
    import warnings
    from erfa import ErfaWarning
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ErfaWarning)
except ImportError:
    pass

DATA_PATH = join(__path__[0], 'data')
LOG_FORMATS = {'conlog_format': "{asctime} - {levelname} - {module} - {message}",
               'filelog_format': "{asctime} - {levelname} - {module} - {message}"}
LOG_FILENAME = 'odslog'


POSTING = {
    'testing': {
        'project': './test_proj.json',
        'upload': './test_upload.json'
        },
    'ata': {
        'project': "/opt/mnt/share/ods_project/ods_rados.json",
        'upload': "/opt/mnt/share/ods_upload/ods.json"
        }
     }