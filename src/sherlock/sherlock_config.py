# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configuration for Sherlock."""

import dataclasses

PERFETTO_CMD = 'perfetto'
TRACES_DEVICE_DIR = '/data/misc/perfetto-traces/'
TRACES_EXTENSION = 'pftrace'


@dataclasses.dataclass
class SherlockConfig:
    """Configuration for Sherlock.

    Attributes:
        local_output_dir: directory path where results are stored
        trace_config_file_path: TraceConfig configuration file path needed by Perfetto
        perfetto_cmd: binary name of the Perfetto tool
        trace_device_dir: directory path where Perfetto traces are stored on an Android
            device
    """

    local_output_dir: str
    trace_config_file_path: str
    perfetto_cmd: str = PERFETTO_CMD
    trace_device_dir: str = TRACES_DEVICE_DIR

    @property
    def trace_remote_output_dir(self) -> str:
        if not self.trace_device_dir.endswith('/'):
            return f'{self.trace_device_dir}'
        return self.trace_device_dir[:-1]

    @property
    def trace_local_output_dir(self) -> str:
        if not self.local_output_dir.endswith('/'):
            return f'{self.local_output_dir}'
        return self.local_output_dir[:-1]
