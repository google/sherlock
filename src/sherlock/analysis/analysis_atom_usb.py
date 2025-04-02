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

"""Extracts USB device attach info from Perfetto traces.

It queries the trace for 'usb_device_attached' slices and their associated
arguments to construct UsbAttachedEvent objects. These objects contain details
such as vendor ID, product ID, whether the device has audio, HID, or storage
interfaces, its current state, and the duration of the last connection.
"""
import dataclasses
import json
import logging
import textwrap

from perfetto.trace_processor import TraceProcessor
from sherlock import trace_analysis


DETECT_ATTACHED_EVENT = 'detect_attached_event'
PERFETTO_QUERY_SLICE_ID = 'SELECT id AS slice_id FROM slice'


@dataclasses.dataclass
class UsbAttachedEvent:
  """Represents a USB device attached event with relevant details."""

  slice_id: int = -1
  timestamp: int = -1
  vendor_id: int = -1
  product_id: int = -1
  has_audio: bool = False
  has_hid: bool = False
  has_storage: bool = False
  state: str = ''
  last_connect_duration_millis: int = -1


def _perfetto_atom_usb_query(event_name: str, slice_id: int) -> str:
  """Generates Perfetto SQL query for a given event within a slice.

  Args:
      event_name: The name of the event to query.
      slice_id: The ID of the slice containing the event.

  Returns:
      A string containing the Perfetto SQL query.
  """
  return textwrap.dedent(f"""
        SELECT
            slice.id AS slice_id,
            slice.ts AS timestamp,
            slice.name AS event_name,
            args.key,
            args.value_type,
            args.int_value,
            args.string_value,
            args.real_value,
            args.display_value
        FROM
            slice
        JOIN
            args ON slice.arg_set_id = args.arg_set_id
        WHERE
            event_name = "{event_name}"
            AND
            slice_id = {slice_id}
        """)


def _detect_attached_event(tp: TraceProcessor) -> list[UsbAttachedEvent]:
  """Detects and extracts USB device attached events from a Perfetto trace.

  Args:
     tp (TraceProcessor): The trace processor.

  Returns:
      list[UsbAttachedEvent]: A list of UsbAttachedEvent objects representing
      the detected events.
  """
  logging.debug('Running detection: %s', DETECT_ATTACHED_EVENT)
  usb_attached_events: list[UsbAttachedEvent] = []
  qr_it = tp.query(PERFETTO_QUERY_SLICE_ID)
  slice_ids = [row.slice_id for row in qr_it]
  for slice_id in slice_ids:
    usb_attached_event = UsbAttachedEvent(slice_id=slice_id)
    qr_it = tp.query(
        _perfetto_atom_usb_query(
            event_name='usb_device_attached', slice_id=slice_id
        )
    )
    for row in qr_it:
      if usb_attached_event.timestamp == -1:
        usb_attached_event.timestamp = row.timestamp
      if row.key == 'usb_device_attached.vid':
        usb_attached_event.vendor_id = row.int_value
      elif row.key == 'usb_device_attached.pid':
        usb_attached_event.product_id = row.int_value
      elif row.key == 'usb_device_attached.has_audio':
        usb_attached_event.has_audio = bool(row.int_value)
      elif row.key == 'usb_device_attached.has_hid':
        usb_attached_event.has_hid = bool(row.int_value)
      elif row.key == 'usb_device_attached.has_storage':
        usb_attached_event.has_storage = bool(row.int_value)
      elif row.key == 'usb_device_attached.state':
        usb_attached_event.state = row.string_value
      elif row.key == 'usb_device_attached.last_connect_duration_millis':
        usb_attached_event.last_connect_duration_millis = row.int_value
    if usb_attached_event.timestamp != -1:
      usb_attached_events.append(usb_attached_event)
  return usb_attached_events


class TraceAnalysisModuleResultAtomUsb(json.JSONEncoder):
  """A custom JSON encoder for TraceAnalysisModuleAtomUsb results.

  This encoder handles the serialization of specific dataclass objects
  used within the module's results.
    - analysis_atom_usb.UsbAttachedEvent
  """

  def default(self, o):
    if isinstance(o, (UsbAttachedEvent,)):
      return dataclasses.asdict(o)
    return super().default(o)


class TraceAnalysisModuleAtomUsb(trace_analysis.TraceAnalysisModule):
  """Analyzes a Perfetto trace to detect and extract USB attached events."""

  MODULE_NAME = 'ANALYSIS_ATOM_USB'

  def __init__(self):
    super().__init__()
    self.module_name = TraceAnalysisModuleAtomUsb.MODULE_NAME
    self.trace_filepath = ''

  def run(
      self, trace_filepath: str
  ) -> trace_analysis.TraceAnalysisModuleResult:
    trace_processor = TraceProcessor(trace=trace_filepath)
    results = {
        DETECT_ATTACHED_EVENT: _detect_attached_event(trace_processor),
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
          cls=TraceAnalysisModuleResultAtomUsb,
          indent=4,
      )
      logging.info(
          '%s report analysis for %s saved in %s',
          self.module_name,
          self.trace_filepath,
          report_filepath,
      )
