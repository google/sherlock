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

"""This module is responsible for running the analysis modules over the traces.

It will iterate over the traces found locally and for each trace, it will run
the analysis modules selected by the user.
The user can select the analysis modules to run using the `TraceAnalysisMode` enum.
The available analysis modules are:
- `ANALYSIS_ALL`: runs all the analysis modules
- `ANALYSIS_URL`: runs only the analysis module for the URLs visited

The results of the analysis are saved in a JSON file with the following name:
`<trace_filepath>-<analysis_module_name>-report.json`
"""

import collections
import logging
import os

from sherlock import sherlock_config
from sherlock import trace_analysis


class TraceAnalysis:
    """Runs the analysis modules over the traces.

    Attributes:
        sherlock_config (sherlock_config.SherlockConfig):  Sherlock configuration settings
        analysis_module_classes (list[trace_analysis.TraceAnalysisMode]): List of analysis modules to run
    """
    def __init__(self,
                 config: sherlock_config.SherlockConfig,
                 analysis_module_classes: list[trace_analysis.TraceAnalysisModule]):
        self.sherlock_config = config
        self.analysis_module_classes: list[trace_analysis.TraceAnalysisModule] = analysis_module_classes

    def _local_trace_filepath(self) -> dict[str, list[str]]:
        """Get the trace files found locally.

        Returns:
            dict[str, list[str]]: A dictionary where the keys are the serial numbers and the values are the
            list of trace files associated with that serial number.
        """
        trace_filepath_by_serial: dict[str, list[str]] = collections.defaultdict(list)
        try:
            content = os.listdir(self.sherlock_config.trace_local_output_dir)
            serial_dirs = [entry for entry in content if os.path.isdir(os.path.join(
                self.sherlock_config.trace_local_output_dir, entry))]
            for serial_dir in serial_dirs:
                trace_filepath_by_serial[serial_dir] = []
        except FileNotFoundError as e:
            logging.warning(e)
            return {}
        for serial_dir in trace_filepath_by_serial:
            try:
                serial_dir_path = os.path.join(self.sherlock_config.trace_local_output_dir, serial_dir)
                content = os.listdir(serial_dir_path)
                for entry in content:
                    if os.path.isfile(os.path.join(serial_dir_path, entry)) and entry.endswith(
                            f'.{sherlock_config.TRACES_EXTENSION}'):
                        trace_filepath_by_serial[serial_dir].append(os.path.join(serial_dir_path, entry))
            except FileNotFoundError:
                pass
        return trace_filepath_by_serial

    def run_analysis(self, filter_by_serials: list[str] = []):
        """Run the analysis modules on the traces.

        Args:
            filter_by_serials (list[str], optional): List of serial numbers to filter the traces. Defaults to [].
        """
        trace_filepath_by_serial = self._local_trace_filepath()
        if filter_by_serials:
            trace_filepath_by_serial = {serial: trace_filepath_by_serial[serial] for serial in filter_by_serials if
                                        serial in trace_filepath_by_serial}
        for serial in trace_filepath_by_serial:
            logging.debug('serial: %s', serial)
            for trace_filepath in trace_filepath_by_serial[serial]:
                logging.debug('trace filepath: %s', trace_filepath)
                for analysis_module_class in self.analysis_module_classes:
                    analysis_module = analysis_module_class()
                    logging.debug('module: %s', analysis_module.module_name)
                    analysis_module_result = analysis_module.run(trace_filepath)
                    basename_fullpath, _ = os.path.splitext(trace_filepath)
                    report_filepath = f'{basename_fullpath}-{analysis_module.module_name}-report.json'
                    analysis_module.write_json_results(report_filepath, analysis_module_result)
