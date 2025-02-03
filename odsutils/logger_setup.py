import logging


CONSOLE_HANDLER_NAME = 'Console'
FILE_HANDLER_PREFIX = 'File_'


class Logger:
    def __init__(self, logger, conlog='INFO', filelog=False,
                 log_filename='default_log_filename', path=None,
                 conlog_format="{asctime} - {levelname} - {module} - {message}",
                 filelog_format="{asctime} - {levelname} - {module} - {message}"):
        self.conlog = conlog.upper() if isinstance(conlog, str) else False
        self.filelog = filelog.upper() if isinstance(filelog, str) else False
        self.log_filename = log_filename
        file_handler_name = f"{FILE_HANDLER_PREFIX}{log_filename}"
        self.path = '' if path is None else path
        self.handler_names = [x.get_name() for x in logger.handlers]
        if CONSOLE_HANDLER_NAME not in self.handler_names and isinstance(conlog, str):
            from sys import stdout
            console_handler = logging.StreamHandler(stdout)
            console_handler.setLevel(self.conlog)
            console_handler.setFormatter(logging.Formatter(conlog_format, style='{', datefmt='%Y-%m-%dT%H:%M:%S'))
            console_handler.set_name(CONSOLE_HANDLER_NAME)
            logger.addHandler(console_handler)
        if file_handler_name not in self.handler_names and isinstance(filelog, str):
            import os.path as op
            file_handler = logging.FileHandler(op.join(path, log_filename), mode='a')
            file_handler.setLevel(self.filelog)
            file_handler.setFormatter(logging.Formatter(filelog_format, style='{', datefmt='%Y-%m-%dT%H:%M:%S'))
            file_handler.set_name(file_handler_name)
            logger.addHandler(file_handler)