#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, with_statement

# python lib
import os
import time
import socket
import logging

# 3rd party lib
import tornado
import tornado.ioloop
import tornado.iostream
import tornado.options
from tornado import gen

# Use tornado default application log.
app_log = logging.getLogger('tornado.application')


class DockerEvent(object):

    def __init__(self):
        self._sep = False
        self._num_read = -1
        self._data = b''

    @gen.coroutine
    def start(self):
        # Create unix socket to `/var/run/docker.sock`.
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect('/var/run/docker.sock')

        # Send HTTP request.
        stream = tornado.iostream.IOStream(sock)
        stream.set_nodelay(True)

        # Read until 365 days passed.
        until = int(time.time()) + 60 * 60 * 24 * 365

        # Request Docker events.
        yield stream.write(u'GET /events?{} HTTP/1.1\r\n\r\n'.format(until).encode('utf-8'))

        # Get response HTTP 200.
        data = yield stream.read_until(b'\n')
        if data != b'HTTP/1.1 200 OK\r\n':
            app_log.error('HTTP Connection Failed...')
            return
        app_log.info('HTTP Connected...')

        # Keep pulling the events.
        while True:
            data = yield stream.read_until(b'\n')

            # Get b'\r\n'.
            if not self._sep and data == b'\r\n':
                self._sep = True

            # Get number of bytes b'171'.
            elif self._sep and self._num_read == -1:
                self._num_read = int(data.decode('utf-8').strip(), 16)

            # Get data stream.
            elif self._sep and self._num_read != -1:
                self._data = data

                app_log.info('number of bytes: {}'.format(len(data)))
                app_log.info('string: {}'.format(data.decode('utf-8')))

                # Clear
                self._sep = False
                self._num_read = -1
                self._data = b''


def main():
    # Enable tornado log.
    tornado.options.parse_command_line()

    # Start Docker events.
    DockerEvent().start()

    # Start tornado.
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()

