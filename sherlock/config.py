
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

PERFETTO_CMD = 'perfetto'
DEVICE_DIR = '/data/misc/perfetto-traces/'

class Config:
    def __init__(self, filename, output_dir, perfetto_cmd=PERFETTO_CMD, device_dir=DEVICE_DIR) -> None:
        self.filename = filename
        self.output_dir = output_dir
        
        self.perfetto_cmd = perfetto_cmd
        self.device_dir = device_dir