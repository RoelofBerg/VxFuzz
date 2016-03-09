#! /usr/bin/env python
# coding: utf-8
#
# Author: Yannick Formaggio
import sys
import ConfigParser
import argparse
import logging

# Kitty imports
from katnip.targets.tcp import *
from kitty.fuzzers import ServerFuzzer
from kitty.interfaces.web import WebInterface
from kitty.model import GraphModel

# Fuzzer imports
from controller import *
from monitor import *
from model import *


# logging levels dict
levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}


class Fuzz(object):

    @staticmethod
    def parse_args():

        parser = argparse.ArgumentParser(
            prog="fuzz",
            description="Kitty based VxWorks network protocol fuzzer",
            epilog="Returns 0 when completed successfully, -1 otherwise"
        )

        # Mandatory args
        mandatory = parser.add_argument_group("Mandatory")
        mandatory.add_argument("-t", "--target_addr", metavar="xxx.xxx.xxx.xxx", dest="target_addr",
                               required=True, type=str)
        mandatory.add_argument("-v", "--target_version", dest="target_version", required=True, type=int,
                               choices=[5, 6])
        mandatory.add_argument("-p", "--target_port", dest="target_port", required=True, type=int)

        # Optional arguments
        opt = parser.add_argument_group("Optional")
        opt.add_argument("-l", "--log_level", dest="log_level", default="error", type=str,
                         choices=[choice for choice in levels.keys()])

        return parser.parse_args()

    @staticmethod
    def parse_config():
        """ Parses the fuzz.ini file
        :return: parsed config file
        """
        conf = ConfigParser.SafeConfigParser(allow_no_value=True)
        conf.read("fuzz.ini")

        return conf

    @staticmethod
    def logger(level, name, logfile):
        """ Create and configure file and console logging.
        :param level: console debugging level only.
        :param name: logger name
        :param logfile: log destination file name
        :return: configured logging object
        """
        logger = logging.getLogger(name)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    @classmethod
    def main(cls):
        """ Main fuzzing routine.
        :return:
        """
        args = cls.parse_args()
        conf = cls.parse_config()
        logger = cls.logger(levels[args.log_level], "tPortmapd.fuzz", "./session.log")
        victim = args.target_addr
        port = args.target_port
        version = args.target_version
        vmrun = conf.get("VMWARE", "vmrun")
        vmx = conf.get("VMWARE", "vm_path")
        snapshot_name = conf.get("VMWARE", "snapshot")
        web_port = conf.getint("KITTY", "web_port")

        to_log = "Started VxWorks {}.x fuzzing session\n".format(version)
        to_log += "Target:\n\tip address: {}\n\tport: {}\n".format(victim, port)
        to_log += "VM: {}\nsnapshot: {}\n".format(vmx, snapshot_name)
        logger.info(to_log)

        # Define target
        target = TcpTarget("tPortmapd", logger=logger, host=victim, port=port, timeout=2)

        # Define the controller
        controller = VmWareController(name="VMWare Controller", logger=logger, vmrun_path=vmrun, vmx_path=vmx,
                                      snap_name=snapshot_name, target_addr=victim, target_port=port)
        target.set_controller(controller)

        # Define the monitor
        monitor = VxWorksProcessMonitor(name="VxWorks Process Monitor", logger=logger, target_addr=victim,
                                        target_version=version)
        target.add_monitor(monitor)

        # Define the model
        model = GraphModel()
        model.connect(portmap_proc_null)

        # Define the fuzzing session
        fuzzer = ServerFuzzer(name="PortmapFuzzer", logger=logger)
        fuzzer.set_interface(WebInterface(port=web_port))
        fuzzer.set_model(model)
        fuzzer.set_target(target)
        fuzzer.set_delay_between_tests(0)

        # Start!
        try:
            fuzzer.start()

        except KeyboardInterrupt:
            logger.info("Session interrupted by user...")
            fuzzer.stop()
            return 1

        except Exception as exc:
            logger.error(exc)
            fuzzer.stop()
            return -1


if __name__ == '__main__':
    sys.exit(Fuzz.main())
