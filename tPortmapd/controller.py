#! /usr/bin/env python
# coding: utf-8
#
# Author: Yannick Formaggio
import os
import time
import socket
import subprocess
from kitty.controllers.base import BaseController


class VmWareController(BaseController):
    """
    This controller controls a virtual machine running in VMWare by
    using the vmrun CLI.
    """
    def __init__(self, name, logger, vmrun_path, vmx_path, snap_name, target_addr, target_port):
        """ Initialize required fields and starts the VM at 'snap_name' state.
        :param name: name of the object
        :param logger: logger for the object
        :param vmrun_path: path to the vmrun executable
        :param vmx_path: path to your targeted VM
        :param snap_name: name of the snapshot you want to reload
        :param target_addr: IP Address of the target
        :param target_port: targeted port on the target
        """
        super(VmWareController, self).__init__(name, logger)
        self._vmrun_path = os.path.abspath(vmrun_path)
        assert (os.path.exists(self._vmrun_path))
        self._vmrun_name = os.path.basename(vmrun_path)
        self._vmx_path = os.path.abspath(vmx_path)
        assert os.path.exists(self._vmx_path)
        self._vmx_name = os.path.basename(vmx_path)
        self._snapshot_name = snap_name
        self._target = (str(target_addr), int(target_port))

    def _vmcommand(self, command, log_message=None):
        """ Wrapper for used vmrun commands.
        :param command: vmrun command line
        """
        if self.logger and log_message:
            self.logger.debug(log_message)
        return subprocess.check_call(command)

    def _start_vm(self):
        """ Starts the VMWare VM with no gui options
        """
        command = [self._vmrun_path, "start", self._vmx_path, "nogui"]
        return self._vmcommand(command, "Starting the virtual machine {}".format(self._vmx_name))

    def _reload_snapshot(self):
        """ Reloads snapshot
        """
        command = [self._vmrun_path, "revertToSnapshot", self._vmx_path, self._snapshot_name]
        return self._vmcommand(command, "Reloading VM Snapshot: {}".format(self._snapshot_name))

    def _stop_vm(self):
        """ Stops the VM
        """
        command = [self._vmrun_path, "stop", self._vmx_path, "hard"]
        return self._vmcommand(command, "Stopping the virtual machine {}".format(self._vmx_name))

    def _suspend_vm(self):
        """ Suspend VM execution
        """
        command = [self._vmrun_path, "suspend", self._vmx_path, "hard"]
        return self._vmcommand(command, "Suspending the virtual machine {}".format(self._vmx_name))

    def _wait(self):
        """ Adding some time for the VM to come up
        """
        # Wait VM is running
        while not self._is_running():
            time.sleep(0.5)

    def _restart_vm(self):
        """ Restarts the VM and wait for it to be ready.
        """
        self._reload_snapshot()
        self._start_vm()
        self._wait()
        self.setup()

    def _is_running(self):
        """ Test if the VM is actually running by listing the running VMs and looking up the VM name in
        the output.

        :return: True if VM running, False otherwise.
        """
        command = [self._vmrun_path, "list"]
        result = subprocess.check_output(command)
        return self._vmx_path in str(result)

    def _is_target_alive(self):
        """ SYN scan the target specified port.
        :return: True if service alive, False otherwise.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            sock.connect(self._target)
            sock.close()
            return True

        except socket.error:
            return False

    def setup(self):
        super(VmWareController, self).setup()
        self._reload_snapshot()
        self._start_vm()
        if not self._is_running():
            raise Exception("Cannot start the VM")

        if not self._is_target_alive():
            raise Exception("Targeted service is not available")

    def pre_test(self, test_number):
        """ Starts the VmWare VM and setup some report fields.
        If VM is not running or targeted service is down: restart the VM.
        :param test_number: test case to be sent
        """
        super(VmWareController, self).pre_test(test_number)
        if not self._is_running() or not self._is_target_alive():
            self.logger.error("VM is not running or service is down")
            self._restart_vm()

    def post_test(self):
        super(VmWareController, self).post_test()

    def teardown(self):
        """ Called at the end of the fuzzing session.
        """
        super(VmWareController, self).teardown()
        if not self._is_running():
            raise Exception("VM is already stopped or paused")
        self._stop_vm()
