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

import argparse
import importlib
import inspect
import logging
import os
import signal
import time

from sherlock import device_manager
from sherlock import sherlock_analysis
from sherlock import sherlock_config
from sherlock import trace_analysis


def _signal_handler_stop_single_device_monitoring(
    unused_signum, unused_frame, dm: device_manager.DeviceManager
):
  """Signal handler to stop device monitoring.

  This handler is called when SIGINT is received. It stops the device monitoring
  process.

  Args:
      unused_signum: The signal number (unused).
      unused_frame: The current stack frame (unused).
      dm (device_manager.DeviceManager): The DeviceManager instance.
  """
  dm.stop_monitoring_devices()


def _handle_device_manager(args: argparse.Namespace) -> None:
  """Handle device monitoring based on command-line arguments.

  Initialize a DeviceManager, set up a signal handler for SIGINT,
  start device monitoring, and wait for the stop event.

  Args:
      args (argparse.Namespace): Parsed command-line arguments.
  """
  dm = device_manager.DeviceManager(
      config=sherlock_config.SherlockConfig(
          local_output_dir=args.traces_directory,
          trace_config_file_path=args.perfetto_config_file,
      ),
      mode=args.operation,
  )
  signal.signal(
      signal.SIGINT,
      lambda signum, frame: _signal_handler_stop_single_device_monitoring(
          signum, frame, dm
      ),
  )
  logging.info('Start monitoring devices')
  dm.start_monitoring_devices()
  dm.stop_event.wait()
  time.sleep(2)


def _handle_trace_analysis(
    args: argparse.Namespace,
    module_classes: [trace_analysis.TraceAnalysisModule],
) -> None:
  """Handle trace analysis based on command-line arguments.

  Initialize a TraceAnalysis object, and run the analysis using the provided
  module classes.

  Args:
      args (argparse.Namespace): Parsed command-line arguments.
      module_classes (list[trace_analysis.TraceAnalysisModule]): List of
        selected module classes.
  """
  trace_analysis = sherlock_analysis.TraceAnalysis(
      config=sherlock_config.SherlockConfig(
          local_output_dir=args.traces_directory, trace_config_file_path=''
      ),
      analysis_module_classes=module_classes,
  )
  logging.info('Start analysing trace files')
  trace_analysis.run_analysis(filter_by_serials=args.serial)


def _device_manager_mode_type(
    mode_string: str,
) -> device_manager.DeviceManagerMode:
  """Convert a string to a DeviceManagerMode enum value.

  Args:
      mode_string (str): The string representation of the mode.

  Returns:
      device_manager.DeviceManagerMode: The corresponding DeviceManagerMode
      value.

  Raises:
      argparse.ArgumentTypeError: If the mode_string is invalid.
  """
  try:
    return device_manager.DeviceManagerMode[mode_string]
  except KeyError:
    raise argparse.ArgumentTypeError(
        f'Invalid DeviceManagerMode value: {mode_string}'
    )


def _import_available_modules(
    folder_path='sherlock/analysis',
) -> [trace_analysis.TraceAnalysisModule]:
  """Import all analysis modules from the specified folder.

  Args:
      folder_path: The path to the folder containing the modules.

  Returns:
      A list of available module classes.
  """
  module_classes: [trace_analysis.TraceAnalysisModule] = []
  for filename in os.listdir(folder_path):
    if filename.endswith('.py') and not filename.startswith('_'):
      module_name = filename[:-3]
      module = importlib.import_module(
          f'.{module_name}', package=folder_path.replace('/', '.')
      )
      for _, cls in inspect.getmembers(module, inspect.isclass):
        if (
            issubclass(cls, trace_analysis.TraceAnalysisModule)
            and cls != trace_analysis.TraceAnalysisModule
        ):
          module_classes.append(cls)
  return module_classes


def main():
  available_analysis_module_classes = _import_available_modules()
  available_analysis_modules_names = ['ANALYSIS_ALL'] + [
      m.MODULE_NAME for m in available_analysis_module_classes
  ]

  parser = argparse.ArgumentParser(
      description='Launch and analyse Perfetto traces on Android'
  )
  parser.add_argument('-v', '--verbose', action='store_true')
  subparsers = parser.add_subparsers(dest='mode')
  # Device Manager Mode
  device_manager_parser = subparsers.add_parser(
      'device-manager', help='Operation mode for connected devices'
  )
  device_manager_parser.add_argument(
      '-c',
      '--perfetto-config-file',
      required=True,
      help='file path for the Perfetto configuration file',
  )
  device_manager_parser.add_argument(
      '--operation',
      required=True,
      type=_device_manager_mode_type,
      choices=list(device_manager.DeviceManagerMode),
      help='operation mode for connected devices',
  )
  # Trace Analysis Mode
  trace_analysis_parser = subparsers.add_parser(
      'trace-analysis', help='Type of analysis to apply on trace files'
  )
  trace_analysis_parser.add_argument(
      '--module',
      nargs='+',
      required=True,
      type=str,
      choices=available_analysis_modules_names,
      help='type of analysis to apply on trace files',
  )
  trace_analysis_parser.add_argument(
      '-s',
      '--serial',
      nargs='+',
      help=(
          'Serial number of devices. Trace files associated with these devices'
          ' will be analyzed'
      ),
  )
  # Common arguments
  for p in [device_manager_parser, trace_analysis_parser]:
    p.add_argument(
        '--traces-directory',
        required=True,
        help='directory where trace files are stored',
    )
    p.add_argument('-v', '--verbose', action='store_true')

  args = parser.parse_args()
  if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
  else:
    logging.basicConfig(level=logging.INFO)
  match args.mode:
    case 'device-manager':
      _handle_device_manager(args)
    case 'trace-analysis':
      if 'ANALYSIS_ALL' in args.module:
        analysis_module_classes = available_analysis_module_classes
      else:
        analysis_module_classes = [
            m
            for m in available_analysis_module_classes
            if m.MODULE_NAME in args.module
        ]
      _handle_trace_analysis(args, analysis_module_classes)
    case _:
      parser.print_help()


if __name__ == '__main__':
  main()
