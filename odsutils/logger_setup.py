import logging


CONSOLE_HANDLER_NAME = 'Console'
FILE_HANDLER_NAME = 'File'
try:
    from . import LOG_FILENAME
except ImportError:
    LOG_FILENAME = 'default_log_filename'

SOME_FORMATS = {'lmomsg': "{levelname} - {module} - {message}",
                'tlmomsg': "{asctime} - {levelname} - {module} - {message}"}

class Logger:
    def __init__(self, logger, conlog='INFO', filelog=False, log_filename=LOG_FILENAME, path=None,
                 conlog_format="{levelname} - {module} - {message}",
                 filelog_format="{asctime} - {levelname} - {module} - {message}"):
        self.conlog = conlog.upper() if isinstance(conlog, str) else False
        self.filelog = filelog.upper() if isinstance(filelog, str) else False
        conlog_format = SOME_FORMATS[conlog_format] if conlog_format in SOME_FORMATS else conlog_format
        filelog_format = SOME_FORMATS[filelog_format] if filelog_format in SOME_FORMATS else filelog_format
        self.log_filename = log_filename
        self.path = '' if path is None else path
        handler_names = [x.get_name() for x in logger.handlers]
        if CONSOLE_HANDLER_NAME not in handler_names and isinstance(conlog, str):
            from sys import stdout
            console_handler = logging.StreamHandler(stdout)
            console_handler.setLevel(self.conlog)
            console_handler.setFormatter(logging.Formatter(conlog_format, style='{'))
            console_handler.set_name(CONSOLE_HANDLER_NAME)
            logger.addHandler(console_handler)
        if FILE_HANDLER_NAME not in handler_names and isinstance(filelog, str):
            import os.path as op
            file_handler = logging.FileHandler(op.join(path, log_filename), mode='a')
            file_handler.setLevel(self.filelog)
            file_handler.setFormatter(logging.Formatter(filelog_format, style='{'))
            file_handler.set_name(FILE_HANDLER_NAME)
            logger.addHandler(file_handler)