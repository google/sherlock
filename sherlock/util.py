import sys

from loguru import logger

class MyFilter:
    def __init__(self, level:str) -> None:
        self.level = level

    def __call__(self, record):
        return record["level"].no >= logger.level(self.level).no

def set_log(level:str) -> None:
    logger.remove(0)
    my_filter = MyFilter(level)
    logger.add(sys.stderr, filter=my_filter, level=level)