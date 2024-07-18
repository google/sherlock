import sys
import glob

sys.path.append("./sherlock")
import sherlock

from sherlock import trace
from sherlock.analysis import kernel

def main():
    raw_traces = {}
    x  = 0
    for i in glob.glob("./output/kernel/**"):
        raw_traces['extern_device-t%d' % x] = i
        x += 1
    tp = trace.Traces(raw_traces)

    s = sherlock.Sherlock(tp,
                          [kernel.detectPrivilegeEscalation, kernel.detectSuspiciousChildren, kernel.detectPrivilegeProcess])
    print(s)

if __name__ == '__main__':
    main()