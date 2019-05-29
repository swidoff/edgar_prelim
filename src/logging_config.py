import logging.config

logging.config.dictConfig(dict(
    version=1,
    disable_existing_loggers=False,
    formatters={
        'f': {'format': '%(asctime)s %(name)s %(levelname)s %(threadName)s %(message)s'}
    },
    handlers={
        'h': {'class': 'logging.StreamHandler', 'formatter': 'f', 'level': logging.DEBUG}
    },
    root={
        'handlers': ['h'], 'level': logging.INFO,
    },
))


def init_logging(name: str):
    return Logger(name)


class Logger(object):

    def __init__(self, name: str) -> None:
        super().__init__()
        self.logger = logging.getLogger(name)

    def info(self, *vargs):
        self.logger.info(' '.join(map(str, list(vargs))))

    def warn(self, *vargs):
        self.logger.warning(' '.join(map(str, list(vargs))))

    def error(self, *vargs):
        self.logger.error(' '.join(map(str, list(vargs))))

    def exception(self, *vargs):
        self.logger.exception(' '.join(map(str, list(vargs))))
