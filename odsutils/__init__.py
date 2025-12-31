from os.path import join
__version__ = "1.0.0"

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
