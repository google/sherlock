import sys

sys.path.append("./sherlock")
import sherlock

from sherlock import trace, config
from sherlock.analysis import chrome

def main():
    chrome.extractAndSaveJsFiles(trace.Traces(
        {'local-device': 'output/36021FDJG001RQ/2024-07-10_22-01-aca5d9.pftrace'}),
        "output/js/")

if __name__ == '__main__':
    main()