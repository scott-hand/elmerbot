import logging


def configure_logger(logger_name, level, filename=None):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    formatter = logging.Formatter("%(levelname)s:%(asctime)s.%(msecs)03d:%(name)s - %(message)s",
                                  "%Y-%m-%d %H:%M:%S")
    if filename:
        fh = logging.FileHandler(filename)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
