import os
import datetime
import re

from loguru import logger

import subprocess

def adb_direct(cmd, stdin, stdout):
  cmd = ['adb', *cmd]
  setpgrp = None
  if os.name != 'nt':
    # On Linux/Mac, start a new process group so all child processes are killed
    # on exit. Unsupported on Windows.
    setpgrp = lambda: os.setpgrp()
  proc = subprocess.Popen(cmd, stdin=stdin, stdout=stdout, preexec_fn=setpgrp)
  return proc

class PerfettoCmd:
    def __init__(self, device, stopping_event, info_device, config) -> None:
        self.device = device
        self.stopping_event = stopping_event
        self.info_device = info_device
        self.config = config

        self.pid_perfetto_process = -1
        
        cmd = ['shell', self.config.perfetto_cmd, '--background']
        tstamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
        fname = '%s-%s.pftrace' % (tstamp, os.urandom(3).hex())
        self.device_file = self.config.device_dir + fname
        cmd.extend(['-o', self.device_file])
        
        self.cmd = cmd

    def start(self):
        perfetto_pid_started = False
        if self.info_device.get(self.device.serial):
            logger.info(self.device.serial + ": Checking if perfetto is still running on online device")
            if "perfetto" in self.device.shell("ps -p %s -o comm= " % self.info_device.get(self.device.serial)[0]):
                logger.info(self.device.serial + ": Perfetto is still running", self.config.filename)
                self.pid_perfetto_process = self.info_device.get(self.device.serial)[0]
                self.device_file = self.info_device.get(self.device.serial)[1]
                perfetto_pid_started = True
        else:
            logger.info(self.device.serial + ": Checking if another perfetto session was running on online device")
            existing_pid = self.device.shell("pidof perfetto")
            if existing_pid:
                existing_args = self.device.shell("ps -p %s -o ARGS=" % existing_pid)
                if existing_args:
                    existing_device_file = ''
                    for x in existing_args.split(' '):
                        if '/data/misc/perfetto-traces' in x:
                            existing_device_file = x
                            break

            
                self.pid_perfetto_process = str(existing_pid)
                self.device_file = existing_device_file
                perfetto_pid_started = True
                logger.info(self.device.serial + ": Found existing perfetto process " + existing_device_file)
            
        if not perfetto_pid_started:
            self.start_new_perfetto()

        # Wait an external event to stop and collect data
        self.stopping_event.wait()

        logger.info(self.device.serial + ": End of running Perfetto on online device")

    def start_new_perfetto(self):
        logger.info(self.device.serial + ": Running Perfetto on online device", self.config.filename)
        cmd = self.cmd
        cmd += ['-c', '-']

        with open(self.config.filename, 'rb') as f:
            logger.info(self.device.serial + ": Running " + " ".join(cmd))
            proc = adb_direct(cmd, stdin=f, stdout=subprocess.PIPE)
            proc_out = proc.communicate()[0].decode().strip()

            match = re.search(r'^(\d+)$', proc_out, re.M)
            if match is None:
                logger.warning(self.device.serial + ": Failed to read the pid from perfetto --background")
                return
            bg_pid = match.group(1)
            exit_code = proc.wait()

        if exit_code != 0:
            logger.warning(self.device.serial + ": Perfetto invocation failed")
            return

        self.pid_perfetto_process = bg_pid
        logger.info(self.device.serial + ": PID perfetto " + str(self.pid_perfetto_process))
        self.info_device[self.device.serial] = (self.pid_perfetto_process, self.device_file)


