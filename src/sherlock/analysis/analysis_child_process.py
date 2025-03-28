# Copyright 2025 Google LLC
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

"""This module is responsible for identifying and inspecting child processes.

This module provides functions to retrieve the child processes of a given
parent process. This is particularly useful for detecting unexpected or
malicious activity, such as Chrome process spawning child processes.
"""

import dataclasses
import json
import logging

from perfetto.trace_processor import TraceProcessor
from sherlock import trace_analysis


DETECT_GENERIC_CHILD_PROCESS = 'detect_generic_child_process'
DETECT_CHROME_CHILD_PROCESS = 'detect_chrome_child_process'


@dataclasses.dataclass
class Process:
  """Process representation."""
  pid: int
  uid: int
  upid: int
  parent_upid: int
  name: str
  cmdline: str

  def __dict__(self):
    return {
        'pid': self.pid,
        'uid': self.uid,
        'upid': self.upid,
        'parent_upid': self.parent_upid,
        'name': self.name,
        'cmdline': self.cmdline,
    }


def _detect_generic_child_process(
    tp: TraceProcessor, parents_process_name: list[str]
) -> list[Process]:
  """Generic detection of child process from a parent list process.

  Args:
      tp (TraceProcessor): The trace processor.
      parents_process_name (list[str]): A list of process name

  Returns:
      list[Process]: The list of processes created by parents_process_name.
  """
  logging.debug(
      'Running detection: %s. Process = %s',
      DETECT_GENERIC_CHILD_PROCESS,
      parents_process_name,
  )
  joined_parent_names = ', '.join('"' + p + '"' for p in parents_process_name)
  qr_it = tp.query(
      'SELECT p.upid, p.pid, p.name, p.parent_upid, p.uid, p.cmdline '
      'FROM process AS p '
      'WHERE '
      'p.name IN ('
      + joined_parent_names
      + ') OR p.parent_upid IN   (SELECT upid FROM process WHERE name IN ('
      + joined_parent_names
      + '))'
  )
  suspicious_process: list[Process] = []
  for row in qr_it:
    logging.debug('ROW = %s', row)
    suspicious_process.append(
        Process(
            pid=row.pid,
            uid=row.uid,
            upid=row.upid,
            parent_upid=row.parent_upid,
            name=row.name,
            cmdline=row.cmdline,
        )
    )
  return suspicious_process


def _detect_chrome_child_process(tp: TraceProcessor) -> list[Process]:
  """Detect Chrome's child process.

  Args:
      tp (TraceProcessor): The trace processor.

  Returns:
      list[Process]: The list of processes created by Chrome.
  """
  logging.debug('Running detection: %s', DETECT_CHROME_CHILD_PROCESS)
  qr_it = tp.query(
      'SELECT p.upid, p.pid, p.name, p.parent_upid, p.uid, p.cmdline '
      'FROM process AS p '
      'WHERE '
      'p.parent_upid IN '
      '  (SELECT upid FROM process WHERE name LIKE "com.android.chrome%" '
      '  AND name != "com.android.chrome_zygote")'
  )
  suspicious_process: list[Process] = []
  for row in qr_it:
    logging.debug('ROW = %s', row)
    suspicious_process.append(
        Process(
            pid=row.pid,
            uid=row.uid,
            upid=row.upid,
            parent_upid=row.parent_upid,
            name=row.name,
            cmdline=row.cmdline,
        )
    )
  return suspicious_process


class TraceAnalysisModuleResultChildProcessEncoder(json.JSONEncoder):
  """A custom JSON encoder.

  - analysis_child_process.Process
  """

  def default(self, o):
    if isinstance(o, (Process,)):
      return dataclasses.asdict(o)
    return super().default(o)


class TraceAnalysisModuleChildProcess(trace_analysis.TraceAnalysisModule):
  """Detect child process creation."""

  MODULE_NAME = 'ANALYSIS_CHILD_PROCESS'

  def __init__(self):
    super().__init__()
    self.module_name = TraceAnalysisModuleChildProcess.MODULE_NAME
    self.trace_filepath = ''

  def run(
      self, trace_filepath: str
  ) -> trace_analysis.TraceAnalysisModuleResult:
    trace_processor = TraceProcessor(trace=trace_filepath)
    results = {
        DETECT_GENERIC_CHILD_PROCESS: _detect_generic_child_process(
            trace_processor,
            ('/apex/com.android.adbd/bin/adbd', '-/system/bin/sh'),
        ),
        DETECT_CHROME_CHILD_PROCESS: _detect_chrome_child_process(
            trace_processor
        ),
    }
    return trace_analysis.TraceAnalysisModuleResult(
        module_name=self.module_name,
        trace_filepath=trace_filepath,
        results=results,
    )

  def write_json_results(
      self,
      report_filepath: str,
      results: trace_analysis.TraceAnalysisModuleResult,
  ):
    with open(report_filepath, 'w') as json_report:
      json.dump(
          results.to_dict(),
          json_report,
          cls=TraceAnalysisModuleResultChildProcessEncoder,
          indent=4,
      )
      logging.info(
          '%s report analysis for %s saved in %s',
          self.module_name,
          self.trace_filepath,
          report_filepath,
      )
