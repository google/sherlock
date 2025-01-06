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

"""This module is responsible for extracting the URL visited from a trace."""

import json
import logging
from typing import Generator

from perfetto.trace_processor import TraceProcessor
from sherlock import trace_analysis


def _extract_url_information(
    tp: TraceProcessor,
) -> Generator[tuple[int, str], None, None]:
  """Extract URLs visited from the trace processor.

  Args:
      tp (TraceProcessor): The trace processor.

  Yields:
      int, string: entry id in the trace, the url visited.
  """
  qr_it = tp.query('SELECT * FROM __intrinsic_v8_js_script')
  for row in qr_it:
    if row.script_type == 'NORMAL':
      yield row.id, row.name


class TraceAnalysisModuleUrl(trace_analysis.TraceAnalysisModule):
  """Extracts URL visited from a trace.

  Attributes: module_name(str): The name of the analysis module.
      trace_filepath (str): The path of the trace file analysed by this module.
  """

  MODULE_NAME = 'ANALYSIS_URL'

  def __init__(self):
    super().__init__()
    self.module_name = TraceAnalysisModuleUrl.MODULE_NAME
    self.trace_filepath = ''

  def run(
      self, trace_filepath: str
  ) -> trace_analysis.TraceAnalysisModuleResult:
    """Run the module on the trace.

    Args:
        trace_filepath (str): The path to the trace file.

    Returns:
        trace_analysis.TraceAnalysisModuleResult: The result of the module.
    """
    logging.info(
        'Running %s module on trace %s', self.module_name, trace_filepath
    )
    self.trace_filepath = trace_filepath
    results = {}
    for url_id, url in _extract_url_information(
        TraceProcessor(trace=trace_filepath)
    ):
      results[url_id] = {'url': url}
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
    """Write the analysis results to a JSON file.

    Args:
        report_filepath (str): The path to the JSON report file.
        results (trace_analysis.TraceAnalysisModuleResult): The analysis results
          object.
    """
    with open(report_filepath, 'w') as json_report:
      json.dump(results.to_dict(), json_report, indent=4)
      logging.info(
          '%s report analysis for %s saved in %s',
          self.module_name,
          self.trace_filepath,
          report_filepath,
      )
