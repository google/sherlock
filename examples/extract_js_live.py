import sys

sys.path.append("./sherlock")
import sherlock

from sherlock import trace, config
from sherlock.analysis import chrome

def main():
    s = sherlock.AndroidDevices(config.Config('data/log_sherlock.bin', './output/'))
    s.runPerfetto()
    traces = s.collectTraces()

    chrome.extractAndSaveJsFiles(trace.Traces(traces), "output/js/")

if __name__ == '__main__':
    main()