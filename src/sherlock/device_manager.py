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

"""This module is responsible for managing the connected devices.

It uses the adbutils library to interact with the devices.
It will monitor the connected devices and for each new device, it will:
- Terminate the Perfetto tracing session
- Collect the trace files
- Optionally restart the Perfetto tracing session
"""

import enum
import logging
import threading
import time

from adbutils import adb
from sherlock import sherlock_config
from sherlock import sherlock_device


@enum.unique
class DeviceManagerMode(enum.Enum):
    TERMINATE_COLLECT = enum.auto()
    TERMINATE_COLLECT_RESTART = enum.auto()


class DeviceManager:
    """Manages connected devices and their perfetto tracing sessions.

    This class handles the discovery, initialization, and management of
    connected devices. It is responsible for starting and stopping Perfetto
    tracing, collecting traces, and managing device connections.

    Args:
        config: A SherlockConfig object containing configuration settings
        mode: The DeviceManagerMode to use. This determines how the manager
              handles device connections and disconnections
    """
    def __init__(self, config: sherlock_config.SherlockConfig,
                 mode: DeviceManagerMode = DeviceManagerMode.TERMINATE_COLLECT):
        self.sherlock_config = config
        self.mode = mode
        self.connected_devices: dict[str, sherlock_device.ConnectedDevice] = {}
        self.handled_sherlock_devices: dict[str, sherlock_device.ConnectedDevice] = {}
        self.stop_event = threading.Event()

    def start_monitoring_devices(self) -> None:
        """Start a background thread to monitor connected devices.

        This thread continuously checks for new devices, handles them according
        to the configured mode, and removes disconnected devices.
        """
        monitor_thread = threading.Thread(target=self._monitor_connected_devices)
        monitor_thread.daemon = True
        monitor_thread.start()

    def stop_monitoring_devices(self) -> None:
        """Stop the device monitoring thread."""
        logging.debug('Stopping monitoring devices')
        self.stop_event.set()

    def _monitor_connected_devices(self) -> None:
        """Monitor connected devices in a loop.

        This method runs in a separate thread and continuously performs the
        following actions:

        1. Retrieves the list of connected devices.
        2. Removes disconnected devices from the `handled_sherlock_devices` list.
        3. For each newly connected device:
           - Initializes a `ConnectedDevice` object.
           - Executes the actions defined by the `DeviceManagerMode`.
           - Adds the device to the `handled_sherlock_devices` list.
        4. Waits for a specified interval before checking again.
        """
        while not self.stop_event.is_set():
            adb_devices = adb.device_list()
            if adb_devices:
                logging.debug('Device(s) connected: %s', ', '.join([d.serial for d in adb_devices]))
                # Clean up handled_sherlock_devices: remove all non-connected devices
                for handled_serial_device in list(self.handled_sherlock_devices.keys()):
                    if handled_serial_device not in [d.serial for d in adb_devices]:
                        logging.debug('%s is not connected, removing from "handled" list', handled_serial_device)
                        del self.handled_sherlock_devices[handled_serial_device]
                # Handle connected devices one at a time
                for device_serial in [d.serial for d in adb_devices]:
                    if device_serial not in self.handled_sherlock_devices:
                        logging.info('Handling device: %s', device_serial)
                        connected_device = sherlock_device.ConnectedDevice(adb.device(device_serial),
                                                                           self.sherlock_config)
                        match self.mode:
                            case DeviceManagerMode.TERMINATE_COLLECT:
                                logging.info('[%s]: start %s mode', device_serial, self.mode.name)
                                logging.debug('Step 1: terminate perfetto program')
                                connected_device.stop_perfetto()
                                logging.debug('Step 2: collect all trace files')
                                connected_device.collect_traces()
                                logging.info('[%s]: end %s mode', device_serial, self.mode.name)
                            case DeviceManagerMode.TERMINATE_COLLECT_RESTART:
                                logging.info('[%s]: start %s mode', device_serial, self.mode.name)
                                logging.debug('Step 1: terminate perfetto program')
                                connected_device.stop_perfetto()
                                logging.debug('Step 2: collect all trace files')
                                connected_device.collect_traces()
                                logging.debug('Step 3: start perfetto program')
                                connected_device.start_perfetto()
                                logging.info('[%s]: end %s mode', device_serial, self.mode.name)
                            case _:
                                logging.warning('Unknown mode: %s, stopping.', self.mode.name)
                                self.stop_event.set()
                        logging.info('Device %s can be disconnected', device_serial)
                        self.handled_sherlock_devices[device_serial] = connected_device
            else:
                self.handled_sherlock_devices = {}
                logging.debug('No device connected')
            time.sleep(3)
        logging.debug('Stopped monitoring devices')
