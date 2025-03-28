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

"""This module is responsible for highlighting crashes.

This module highlights if any tombstones were created during the trace period,
or if any applications crashed.
"""

import dataclasses
import json
import logging
import textwrap

from perfetto.trace_processor import TraceProcessor
from sherlock import trace_analysis


DETECT_APP_CRASHES = 'detect_app_crashes'
DETECT_TOMBSTONES = 'detect_tombstones'


@dataclasses.dataclass
class AppProcessDied:
  """AppProcessDied representation."""
  pid: int
  name: str
  reason: str
  sub_reason: str
  importance: str

  def __init__(self):
    self.pid = 0
    self.name = None
    self.reason = None
    self.sub_reason = None
    self.importance = None

  def __dict__(self):
    return {
        'pid': self.pid,
        'name': self.name,
        'reason': self.reason,
        'sub_reason': self.sub_reason,
        'importance': self.importance,
    }


def _detect_tombstones(
    tp: TraceProcessor
) -> int:
  """Highlight tombstone occurrences.

  Args:
      tp (TraceProcessor): The trace processor.

  Returns:
      int: The number of tombstones created
  """
  logging.debug('Running detection: %s', DETECT_TOMBSTONES)
  # There is no additional data associated with this atom, you just get the
  # indication that a tombstone was created.
  qr_it = tp.query(
      'SELECT name FROM slice WHERE name = "tomb_stone_occurred"'
  )
  tombstone_count = 0
  for row in qr_it:
    logging.debug('ROW = %s', row)
    tombstone_count += 1
  return tombstone_count


def _detect_app_crashes(tp: TraceProcessor) -> list[AppProcessDied]:
  """Detect application crashes.

  Args:
      tp (TraceProcessor): The trace processor.

  Returns:
      list[AppProcessDied]: The list of application crashes.
  """
  logging.debug('Running detection: %s', DETECT_APP_CRASHES)
  qr_it = tp.query(textwrap.dedent("""\
          SELECT args.arg_set_id, args.id, args.flat_key, args.int_value,
          args.string_value FROM args, slice
          WHERE slice.name = "app_process_died" AND
          slice.arg_set_id = args.arg_set_id
          ORDER BY args.arg_set_id, args.id"""))
  app_crashes: list[AppProcessDied] = []
  crash = None
  current_arg_set = -1
  for row in qr_it:
    logging.debug('ROW = %s', row)
    if row.arg_set_id != current_arg_set:
      current_arg_set = row.arg_set_id
      if crash:
        app_crashes.append(crash)
      crash = AppProcessDied()
    if row.flat_key == 'app_process_died.uid':
      crash.pid = row.int_value
    elif row.flat_key == 'app_process_died.process_name':
      crash.name = row.string_value
    elif row.flat_key == 'app_process_died.reason':
      crash.reason = row.string_value
    elif row.flat_key == 'app_process_died.sub_reason':
      crash.sub_reason = row.string_value
    elif row.flat_key == 'app_process_died.importance':
      crash.importance = row.string_value
    elif (
        row.flat_key == 'app_process_died.pss'
        or row.flat_key == 'app_process_died.rss'
        or row.flat_key == 'app_process_died.has_foreground_services'
    ):
      # We don't use these.
      pass
    else:
      raise ValueError(f'Unknown key {row.flat_key}')
  if crash:
    app_crashes.append(crash)

  return app_crashes


class TraceAnalysisModuleResultAppProcessDiedEncoder(json.JSONEncoder):
  """A custom JSON encoder for analysis_crashes.AppProcessDied."""

  def default(self, o):
    if isinstance(o, (AppProcessDied,)):
      return dataclasses.asdict(o)
    return super().default(o)


class TraceAnalysisModuleCrashes(trace_analysis.TraceAnalysisModule):
  """Detect child process creation."""

  MODULE_NAME = 'ANALYSIS_CRASHES'

  def __init__(self):
    super().__init__()
    self.module_name = TraceAnalysisModuleCrashes.MODULE_NAME
    self.trace_filepath = ''

  def run(
      self, trace_filepath: str
  ) -> trace_analysis.TraceAnalysisModuleResult:
    trace_processor = TraceProcessor(trace=trace_filepath)
    results = {
        DETECT_APP_CRASHES: _detect_app_crashes(
            trace_processor,
        ),
        DETECT_TOMBSTONES: _detect_tombstones(
            trace_processor,
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
          cls=TraceAnalysisModuleResultAppProcessDiedEncoder,
          indent=4,
      )
      logging.info(
          '%s report analysis for %s saved in %s',
          self.module_name,
          self.trace_filepath,
          report_filepath,
      )
