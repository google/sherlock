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

from sherlock import trace
from sherlock.analysis import chrome

def main():
    chrome.extractAndSaveJsFiles(trace.Traces(
        {'local-device': 'output/36021FDJG001RQ/2024-07-10_22-01-aca5d9.pftrace'}),
        "output/js/")

if __name__ == '__main__':
    main()