import signal

from loguru import logger

from sherlock import fetcher

class AndroidDevices:
    def __init__(self, config):
        signal.signal(signal.SIGINT, self.signal_handler)

        self.config = config
        self.fetcher = fetcher.Fetcher(self.config)

    def runPerfetto(self):
        logger.info('Running perfetto')
        self.fetcher.runPerfetto()

    def collectTraces(self):
        logger.info('Collecting perfetto traces')
        return self.fetcher.collectTraces()

    def signal_handler(self, sig, frame):
        logger.info("Closing all devices ...")
        self.fetcher.closeAll()
        return
    
class Sherlock:
    def __init__(self, tp, detectors_list) -> None:
        self.tp = tp

        self.results = {}
        for detector in detectors_list:
            self.results[detector.__name__] = detector(tp)

    def __str__(self):
        return 'Sherlock ' + str(self.results.keys())