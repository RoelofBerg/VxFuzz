#! /usr/bin/env python
# coding: utf-8
#
# Author: Yannick Formaggio
from kitty.monitors.base import BaseMonitor
from wdbdbg.dbg import *


class VxWorksProcessMonitor(BaseMonitor):

    def __init__(self, name, logger, target_addr, target_version):
        """
        :param name: name of the object
        :param logger: logger for the object
        :param target_addr: IP Address of the target
        :param target_version: VxWorks OS version
        """
        super(VxWorksProcessMonitor, self).__init__(name, logger)

        self.target = str(target_addr)
        self.target_version = int(target_version)
        self.logger = logger
        self.dbg = None
        self.last_crash = None

    def setup(self):
        """
        Starts the WDB RPC debugger
        """
        self.dbg = Dbg(self.target_version, self.target)
        self.dbg.connect()
        self.dbg.begin_monitoring()
        threading.Thread(target=self.dbg.monitor, name="debug_loop").start()

    def pre_test(self, test_number):
        super(VxWorksProcessMonitor, self).pre_test(test_number)

    def post_test(self):
        """
        Get crash report if any.
        """
        super(VxWorksProcessMonitor, self).post_test()
        time.sleep(0.5)
        if self.dbg.crashed:
            if self.logger:
                self.logger.info("Crash detected")
            self.last_crash = self.dbg.monitor()
            self.report.failed(self.last_crash)
        # self.dbg = None

    def teardown(self):
        if self.dbg:
            self.dbg = None

        super(VxWorksProcessMonitor, self).teardown()

    def _monitor_func(self):
        """
        :return:
        """
        pass

    def _is_alive(self):
        """
        Need to reconnect WDB RPC after each TC, otherwise we never catch the notification.
        :return: False
        """
        return False
