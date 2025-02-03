from importlib.metadata import version
__version__ = version('odsutils')

try:
    import warnings
    from erfa import ErfaWarning
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ErfaWarning)
except ImportError:
    pass

LOG_FORMATS = {'conlog_format': "{asctime} - {levelname} - {module} - {message}",
               'filelog_format': "{asctime} - {levelname} - {module} - {message}"}
LOG_FILENAME = 'odslog'