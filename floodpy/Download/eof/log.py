import logging


def _set_logger_handler(level="INFO"):
    logger.setLevel(level)
    h = logging.StreamHandler()
    h.setLevel(level)
    format_ = "[%(asctime)s] [%(levelname)s %(filename)s] %(message)s"
    fmt = logging.Formatter(format_, datefmt="%m/%d %H:%M:%S")
    h.setFormatter(fmt)
    logger.addHandler(h)


logger = logging.Logger("sentineleof")
logger.addHandler(logging.NullHandler())
# _set_logger_handler()
