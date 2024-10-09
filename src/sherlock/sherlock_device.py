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

"""This module provides functionalities for interacting with Android devices connected via ADB."""

import datetime
import logging
import os
import re
import subprocess
import time

import adbutils
from sherlock import sherlock_config


class ConnectedDeviceAdbCmdError(Exception):
    pass


def _adb_direct(cmd, serial, stdin, stdout):
    cmd = ['adb', '-s', serial, *cmd]
    preexec_fn = None
    if os.name != 'nt':
        # On Linux/Mac, start a new process group so all child processes are killed
        # on exit. Unsupported on Windows.
        preexec_fn = os.setpgrp
    return subprocess.Popen(cmd, stdin=stdin, stdout=stdout, preexec_fn=preexec_fn)


class ConnectedDevice:
    """Represents a connected Android device and provides methods for interacting with it via ADB.

    Attributes:
        adb_device (adbutils.AdbDevice): The `adbutils.AdbDevice` object representing the device
        sherlock_config (sherlock_config.SherlockConfig): Sherlock configuration settings
    """
    def __init__(self, adb_device: adbutils.AdbDevice, sherlock_config: sherlock_config.SherlockConfig):
        self.adb_device: adbutils.AdbDevice = adb_device
        self.sherlock_config = sherlock_config

    @property
    def serial(self) -> str:
        """Get the serial number of the device connected via ADB.

        Returns:
            The device's serial number.
        """
        return self.adb_device.serial

    @property
    def connected(self) -> bool:
        """Check if the device is connected.

        Returns:
            True if the device is connected, False otherwise.
        """
        try:
            _ = self.adb_device.info
        except adbutils.errors.AdbError:
            return False
        return True

    def _build_perfetto_shell_cmd(self, remote_trace_filepath: str):
        """Build the ADB shell command to start perfetto.

        Args:
            remote_trace_filepath: The remote file path where the trace data will be saved.

        Returns:
            A list containing the ADB shell command and its arguments.
        """
        cmd = ['shell', self.sherlock_config.perfetto_cmd, '--background',
               '-o', remote_trace_filepath, '-c', '-']
        return cmd

    def _generate_perfetto_trace_filename(self) -> str:
        """Generate a unique filename for a perfetto trace.

        The filename includes a timestamp, a random suffix, and the file extension
        specified in `sherlock_config.TRACES_EXTENSION`.

        Returns:
            The generated filename, including the directory path on the device.
        """
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        random_suffix = os.urandom(3).hex()
        trace_filename = f'{timestamp}-{random_suffix}.{sherlock_config.TRACES_EXTENSION}'
        return f'{self.sherlock_config.trace_device_dir}/{trace_filename}'

    def _get_running_trace_output_remote_filepath(self) -> str | None:
        """Get the remote file path of the currently running perfetto trace.

        This method retrieves the file path where perfetto is currently writing
        the trace data on the device. It does this by inspecting the command-line
        arguments of the perfetto process.

        Returns:
            The remote file path of the trace if perfetto is running and the path
            can be determined, otherwise None.
        """
        perfetto_pid = self.perfetto_pid()
        if not perfetto_pid:
            logging.debug('[%s]: perfetto is not running', self.serial)
            return None
        try:
            perfetto_cmdline = self.shell(f'ps -p {perfetto_pid} -o ARGS=').lstrip()
            logging.debug('[%s]: perfetto is running with: %s', self.serial, perfetto_cmdline)
            for token in perfetto_cmdline.split(' '):
                if token.endswith(sherlock_config.TRACES_EXTENSION):
                    return token
            return None
        except ConnectedDeviceAdbCmdError:
            return None

    def list_trace_files(self) -> list[str]:
        """List all the trace files stored on the device.

        The directory path comes from the `sherlock_config` object.

        Returns:
            A list of full file paths for all trace files found on the device.
            Returns an empty list if no trace files are found or if there is an error
            communicating with the device.
        """
        try:
            trace_files = [f for f in self.shell(f'ls {self.sherlock_config.trace_remote_output_dir}').split() if
                           f.endswith(sherlock_config.TRACES_EXTENSION)]
            return [f'{self.sherlock_config.trace_remote_output_dir}/{f}' for f in trace_files]
        except ConnectedDeviceAdbCmdError:
            return []

    def shell(self, cmd: str) -> str:
        """Execute an ADB shell command on the device.

        Args:
            cmd (str): The shell command to execute.

        Returns:
            The output of the command.

        Raises:
            ConnectedDeviceAdbCmdError: If there is an error communicating with the device or executing the command.
        """
        try:
            return self.adb_device.shell(cmd)
        except adbutils.errors.AdbError:
            logging.warning('[%s]: unable to execute ADB shell <%s>', self.serial, cmd)
            raise ConnectedDeviceAdbCmdError()

    def perfetto_pid(self) -> int:
        """Get the process ID (PID) of perfetto on the device.

        Returns:
            The PID of perfetto if found, otherwise 0.
        """
        try:
            perfetto_pid = int(self.shell('pidof perfetto'))
            logging.debug('[%s]: perfetto PID=%d', self.serial, perfetto_pid)
            return perfetto_pid
        except (ValueError, ConnectedDeviceAdbCmdError):
            logging.debug('[%s]: unable to find perfetto PID', self.serial)
            return 0

    def start_perfetto(self) -> bool:
        """Start a perfetto tracing session on the device.

        This method starts a perfetto tracing session using the configuration
        specified in the `trace_config_file_path` from the `sherlock_config` object.

        Returns:
            True if perfetto was started successfully, False otherwise.
        """
        if self.perfetto_pid():
            logging.debug('[%s] perfetto is already running with PID=%d', self.serial, self.perfetto_pid())
            return False
        logging.debug('[%s]: starting perfetto', self.serial)
        with open(self.sherlock_config.trace_config_file_path, 'rb') as f:
            remote_trace_filepath = self._generate_perfetto_trace_filename()
            adb_perfetto_command_line = self._build_perfetto_shell_cmd(remote_trace_filepath)
            proc = _adb_direct(adb_perfetto_command_line, self.serial, stdin=f, stdout=subprocess.PIPE)
            proc_out = proc.communicate()[0].decode().strip()
            match = re.search(r'^(?P<pid>\d+)$', proc_out, re.MULTILINE)
            if match is None:
                logging.warning('[%s]: failed to read the pid from `perfetto --background`', self.serial)
                return False
            perfetto_pid = match.group('pid')
            exit_code = proc.wait()
            if exit_code != 0:
                logging.warning('[%s]: perfetto invocation failed', self.serial)
                return False
            logging.info('[%s]: perfetto has started with PID = %s', self.serial, perfetto_pid)
            return True

    def stop_perfetto(self) -> None:
        """Stop the perfetto tracing session on the device.

        This method attempts to gracefully stop the perfetto process by sending a
        TERM signal. It then waits for the process to terminate.
        """
        logging.debug('[%s]: stopping perfetto', self.serial)
        perfetto_pid = self.perfetto_pid()
        if not perfetto_pid:
            logging.info('[%s]: perfetto was not running', self.serial)
        else:
            logging.debug('[%s]: terminate perfetto process with PID=%d', self.serial, perfetto_pid)
            self.shell(f'kill -TERM {perfetto_pid}')
            while self.perfetto_pid():
                time.sleep(.5)
            logging.info('[%s]: perfetto (PID=%s) has been terminated', self.serial, perfetto_pid)

    def collect_traces(self, filename_filter=lambda x: True, delete_after_transfer=True) -> None:
        """Collect perfetto trace files from the device.

        This method retrieves trace files from the device and stores them in the
        local output directory specified in the `sherlock_config` object.

        Args:
            filename_filter: A function that takes a filename as input and returns
                             True if the file should be collected, False otherwise.
                             Defaults to a function that accepts all files.
            delete_after_transfer: If True, delete the trace files from the device
                                   after they are transferred. Defaults to True.
        """
        local_output_dirpath = os.path.join(self.sherlock_config.local_output_dir, self.serial)
        try:
            os.makedirs(local_output_dirpath, exist_ok=True)
            # Pull all the remote traces on the device if their filename satisfy the filename_filter
            if not self.list_trace_files():
                logging.info('[%s]: no trace files found', self.serial)
                return
            for trace_filepath in self.list_trace_files():
                if filename_filter(trace_filepath):
                    logging.debug('[%s]: collecting %s trace file', self.serial, trace_filepath)
                    self.adb_device.sync.pull(trace_filepath,
                                              f'{local_output_dirpath}{os.path.sep}{os.path.basename(trace_filepath)}')
                    logging.info('[%s]: trace %s saved in %s', self.serial, trace_filepath, local_output_dirpath)
                    if delete_after_transfer:
                        self.shell(f'rm -f {trace_filepath}')
                        logging.debug('[%s]: trace %s deleted', self.serial, trace_filepath)
        except PermissionError:
            logging.warning('[%s]: permission denied: Unable to create directory %s', self.serial, local_output_dirpath)
        except OSError as e:
            logging.error('[%s]: error creating directory %s: %s', self.serial, local_output_dirpath, e)
        except adbutils.errors.AdbError as e:
            logging.error('[%s]: error on the device: %s', self.serial, e)
