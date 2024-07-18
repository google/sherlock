import threading
import time
import queue
import os
import datetime

import adbutils
from adbutils import adb
from loguru import logger

from sherlock import perfetto

def online_device_watcher(stopping_threads, devices_list, onqueue_devices, info_device, config):
    while True:
        if stopping_threads.is_set():
            break
        logger.info("[THREAD] Fetching new devices ...")
        for d in adb.device_list():
            if d.serial not in devices_list:
                device = OnlineDevice(d.serial, devices_list, info_device, config)
                device.start()
                devices_list[d.serial] = device
                onqueue_devices.put(device)
        time.sleep(2)

    logger.debug("[THREAD] End online_device_watcher")

def delete_device_watcher(stopping_threads, devices_list, onqueue_devices):
    while True:
        if stopping_threads.is_set():
            break

        list_to_del = []
        for d in devices_list.keys():
            try:
                devices_list[d].online()
            except adbutils.errors.AdbError as e:
                devices_list[d].error = e
                list_to_del.append(d)

        for d in list_to_del:
            deleted_serial = devices_list[d].serial
            adb_error = devices_list[d].error
            devices_list[d].stop()
            del devices_list[d]
            logger.warning("[THREAD] Deleted device %s %s" % (deleted_serial, adb_error))

        time.sleep(0.5)
    logger.debug('[THREAD] End delete_device_watcher')

class OnlineDevice(threading.Thread):
    def __init__(self, serial, devices_list, info_device, config) -> None:
        logger.info('Adding new online device', serial)
        self.serial = serial
        threading.Thread.__init__(self)
        self.d = adb.device(serial)
        self.devices_list = devices_list
        self.info_device = info_device
        self.config = config
        
        self.connected = True
        self.start_perfetto = False
        self.perfetto_cmd = None
        self.error = None

        self.uid = self.serial + datetime.datetime.now().strftime('-%Y-%m-%d_%H-%M')

    def online(self):
        self.d.shell("getprop ro.serial")

    def run(self):
        while True:
            if not self.connected:
                break

            try:
                if self.start_perfetto:
                    self.start_perfetto = False
                    self.stopping_event = threading.Event()
                    self.perfetto_cmd = perfetto.PerfettoCmd(self.d, self.stopping_event, self.info_device, self.config)
                    self.perfetto_cmd.start()
                    self.connected = False
            except adbutils.errors.AdbError as e:
                logger.warning('ADB error with device ', self.d.serial)
                self.devices_list.discard(self.d.serial)
                self.connected = False
        
        logger.warning(self.serial, ": is disconnected: ")

    def startPerfetto(self):
        logger.info(self.serial + ": Starting Perfetto")
        self.start_perfetto = True

    def stop(self):
        logger.info(self.serial + ": Stopping to wait for Perfetto")
        self.stopping_event.set()

    def stopPerfetto(self):
        logger.info(self.serial + ": Stopping Perfetto")
        
        if self.perfetto_cmd:
            self.stopping_event.set()

        # Stop
        self.connected = False

    def getTrace(self):
        logger.info(self.serial + ": Collecting Perfetto Trace")

        logger.info(self.serial + ": Killing perfetto PID " + str(self.perfetto_cmd.pid_perfetto_process))
        self.d.shell(['kill', '-TERM', str(self.perfetto_cmd.pid_perfetto_process)])

        host_directory = os.path.join(self.config.output_dir, self.serial)
        try:
            os.mkdir(host_directory)
        except FileExistsError as e:
            logger.warning(e)
        host_file = os.path.join(host_directory, os.path.basename(self.perfetto_cmd.device_file))
        self.d.sync.pull(self.perfetto_cmd.device_file, host_file)

        logger.info(self.serial + ": End of collecting Perfetto Trace")

        return host_file

class Fetcher:
    def __init__(self, config) -> None:
        self.config = config
        self.onqueue_devices = queue.Queue()
        self.devices_list = {}
        self.info_device = {}
        self.stopping_threads = threading.Event()

        self.online_device_watcher_thread = threading.Thread(target=online_device_watcher, 
                                                             args=(self.stopping_threads, self.devices_list, self.onqueue_devices, self.info_device, self.config))
        self.online_device_watcher_thread.start()

        self.delete_device_watcher_thread = threading.Thread(target=delete_device_watcher,
                                                             args=(self.stopping_threads, self.devices_list, self.onqueue_devices,))
        self.delete_device_watcher_thread.start()

    def runPerfetto(self):
        while True:
            if self.stopping_threads.is_set():
                break

            try:
                device = self.onqueue_devices.get(block=True, timeout=1)
                device.startPerfetto()
            except Exception as ex:
                if self.stopping_threads.is_set():
                    return

        logger.debug("End runPerfetto")

    def collectTraces(self):
        logger.info("Collecting traces on all online devices")

        traces = {}
        for device in self.devices_list:
             traces[self.devices_list[device].uid] = self.devices_list[device].getTrace()
        return traces

    def closeAll(self):
        logger.info("Closing all online devices")
        self.stopping_threads.set()
        for device in self.devices_list:
            self.devices_list[device].stopPerfetto()