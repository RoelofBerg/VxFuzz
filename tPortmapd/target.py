#! /usr/bin/env python
# coding: utf-8
#
# Author: Yannick Formaggio
import socket
from kitty.targets.server import ServerTarget


class TcpTarget(ServerTarget):
    """ TcpTarget is implementation of a TCP target for the ServerFuzzer
    """

    def __init__(self, name, host, port, timeout=None, logger=None):
        """
        :param name: name of the object
        :param host: hostname of the target
        :param port: port of the target
        :param timeout: socket timeout (default: None)
        :param logger: logger for this object (default: None)
        """
        # Call ServerTarget constructor
        super(TcpTarget, self).__init__(name, logger)

        # Define hostname and port of the target
        if host is None or port is None:
            raise ValueError("Missing host or port values")
        self.host = str(host)
        self.port = int(port)

        # Socket timeout
        self.timeout = timeout

        # The socket itself
        self.socket = None

    @staticmethod
    def _get_socket():
        """ Get a socket object
        :return: socket object
        """
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def pre_test(self, test_num):
        """ Prepare to the test, create the socket.
        :param test_num: number of the test case to be sent.
        """
        # Call the super class (report preparation, etc.)
        super(TcpTarget, self).pre_test(test_num)

        # Create the socket if it does not exists
        if not self.socket:
            sock = self._get_socket()
            # Set timeout
            if self.timeout:
                sock.settimeout(self.timeout)

            # Connect
            sock.connect((self.host, self.port))

            self.socket = sock

    def post_test(self, test_num):
        """ Called after a test is completed, perform cleanup, etc.
        :param test_num: number of the test case sent
        """
        super(TcpTarget, self).post_test(test_num)
        if self.socket:
            self.socket.close()
            self.socket = None

    def _send_to_target(self, payload):
        self.socket.send(payload)

    def _receive_from_target(self):
        return self.socket.recv(10000)
