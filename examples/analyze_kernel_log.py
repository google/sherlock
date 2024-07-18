# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob

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