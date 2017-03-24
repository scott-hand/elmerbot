import appdirs
import logging
import os


def build_logger(logger_name, filename=None, log_to_stdout=True, log_to_file=True, file_level=logging.INFO,
                 stdout_level=logging.INFO):
    """This factory method builds consistent logging objects for various classes to use.
    """
    logger = logging.getLogger(logger_name)
    filename = filename or "statuslog"
    
    if not logger.handlers:
        formatter = logging.Formatter("%(levelname)s:%(asctime)s.%(msecs)03d:%(name)s - %(message)s",
                                       "%Y-%m-%d %H:%M:%S")
        if log_to_file:
            log_path = appdirs.user_log_dir("elmerbot")
            if not os.path.exists(log_path):
                os.makedirs(log_path)
            fh = logging.FileHandler(os.path.join(log_path, filename))
            fh.setFormatter(formatter)
            fh.setLevel(file_level)
            logger.addHandler(fh)
        if log_to_stdout:
            sh = logging.StreamHandler()
            sh.setFormatter(formatter)
            sh.setLevel(stdout_level)
            logger.addHandler(sh)
        errors = logging.FileHandler(os.path.join(log_path, "errorlog"))
        errors.setFormatter(formatter)
        errors.setLevel(logging.WARNING)
        logger.addHandler(errors)
    logger.setLevel(logging.INFO)
    return logger
