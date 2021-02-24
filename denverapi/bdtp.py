"""
#Big Data Transfer Protocol
##What does it do

This protocol sends big data on a address (IPv4,port)
without worrying about pipe errors
"""

__author__ = "Xcodz"
__version__ = "2021.2.24"

import abc
import socket
import time
import typing

from . import thread_control

default_buffer_size = 100000


class _BaseSender(abc.ABC):
    @abc.abstractmethod
    def send(self, c):
        pass


class _BaseReceiver(abc.ABC):
    @abc.abstractmethod
    def recv(self, c):
        pass


class DataSenderHost(_BaseSender):
    def __init__(self):
        self.data = b""
        self.address: tuple = ("", 0)
        self.data_send: int = 0
        self.buffer_size: int = default_buffer_size
        self.task = False

    def send(self, connected_socket: socket.socket = None):
        if connected_socket is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(self.address)
            s.listen(5)
            connection, _ = s.accept()
        else:
            connection = connected_socket

        if isinstance(self.data, bytes):
            for line in range(0, len(self.data), self.buffer_size):
                lts = self.data[line : line + self.buffer_size]
                connection.sendall(lts)
                self.data_send += self.buffer_size
        elif isinstance(self.data, typing.BinaryIO):
            while True:
                line = self.data.read(self.buffer_size)
                if line == b"":
                    break
                connection.sendall(line)
                self.data_send += self.buffer_size

        connection.send(b"")
        if connected_socket is None:
            connection.close()
            s.close()
        self.task = True


class DataSenderPort(_BaseSender):
    def __init__(self):
        self.data: bytes = b""
        self.address: tuple = ("", 0)
        self.data_send: int = 0
        self.buffer_size: int = default_buffer_size
        self.task = False

    def send(self, connected_socket: socket.socket = None):
        if connected_socket is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.address)
        else:
            s = connected_socket

        if isinstance(self.data, bytes):
            for x in range(0, len(self.data), self.buffer_size):
                lts = self.data[x : x + self.buffer_size]
                s.sendall(lts)
                self.data_send += self.buffer_size
        elif isinstance(self.data, typing.BinaryIO):
            while True:
                line = self.data.read(self.buffer_size)
                if line == b"":
                    break
                s.sendall(line)
                self.data_send += self.buffer_size

        s.send(b"")
        if connected_socket is None:
            s.close()
        self.task = True


class DataReceiverHost(_BaseReceiver):
    def __init__(self):
        self.address: tuple = ("", 0)
        self.data_recv: int = 0
        self.buffer_size: int = default_buffer_size
        self.data = b""
        self.task = False

    def recv(self, connected_socket: socket.socket = None):
        if connected_socket is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(self.address)
            s.listen(5)
            connection, _ = s.accept()
        else:
            connection = connected_socket
        recv_bytes = b"\0"

        while recv_bytes != b"":
            recv_bytes = connection.recv(self.buffer_size)
            self.data += recv_bytes
            self.data_recv += self.buffer_size

        if connected_socket is None:
            connection.close()
            s.close()
        self.task = True


class DataReceiverPort(_BaseReceiver):
    def __init__(self):
        self.address: tuple = ("", 0)
        self.data_recv: int = 0
        self.buffer_size: int = default_buffer_size
        self.data = b""
        self.task = False

    def recv(self, connected_socket: socket.socket = None):
        if connected_socket is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.address)
            connection = s
        else:
            connection = connected_socket
        recv_bytes = b"\0"

        while recv_bytes != b"":
            recv_bytes = connection.recv(self.buffer_size)
            self.data += recv_bytes
            self.data_recv += self.buffer_size

        if connected_socket is None:
            connection.close()
        self.task = True


def new_send_data_host(data: bytes, addr: tuple, buffer_size=None):
    sender_object = DataSenderHost()
    sender_object.data = data
    sender_object.address = addr
    if buffer_size is not None:
        sender_object.buffer_size = buffer_size
    return sender_object


def new_send_data_port(data: bytes, addr: tuple, buffer_size=None):
    sender_object = DataSenderPort()
    sender_object.data = data
    sender_object.address = addr
    if buffer_size is not None:
        sender_object.buffer_size = buffer_size
    return sender_object


def new_receive_data_host(addr: tuple, buffer_size=None):
    sender_object = DataReceiverHost()
    sender_object.address = addr
    if buffer_size is not None:
        sender_object.buffer_size = buffer_size
    return sender_object


def new_receive_data_port(addr: tuple, buffer_size=None):
    sender_object = DataReceiverPort()
    sender_object.address = addr
    if buffer_size is not None:
        sender_object.buffer_size = buffer_size
    return sender_object


def attach_speed_logger(data_object):
    spl = []

    @thread_control.runs_parallel
    def sps(spl, d: _BaseSender):
        old = 0
        new = 0
        spl.append(d.buffer_size)
        while not d.task:
            time.sleep(0.01)
            new = d.data_send
            spl.append(new - old)
            old = new

    @thread_control.runs_parallel
    def spr(spl, d: _BaseReceiver):
        old = 0
        new = 0
        spl.append(d.buffer_size)
        while not d.task:
            time.sleep(0.01)
            new = d.data_recv
            spl.append(new - old)
            old = new

    (spr if isinstance(data_object, _BaseReceiver) else sps)(spl, data_object)
    return spl


def launch(data_object, connected_socket=None):
    if isinstance(data_object, _BaseSender):
        data_object.send(connected_socket)
    else:
        data_object.recv(connected_socket)


def average_speed_log(spl: list):
    while spl[0] == 0:
        spl.pop(0)
    while spl[-1] == 0:
        spl.pop()
    return (sum(spl) / len(spl)) * 100


def main():
    print("Reading Data")
    datats = open(input("File > "), "r+b").read()
    print("Read Data")
    print("Making Classes")
    sc = new_send_data_port(datats, ("127.0.0.1", 4623))
    rc = new_receive_data_host(("127.0.0.1", 4623))
    spl = attach_speed_logger(rc)
    from threading import Thread

    Thread(target=launch, args=(sc,)).start()
    rc.recv()
    print(len(spl))
    print(
        f"Data Send:\n\tlen: {len(sc.data)}\nData Received:\n\tlen: {len(rc.data)}\n\tis_equal: {rc.data == sc.data}"
    )
    print(f"Average Speed: {average_speed_log(spl)} bytes per second")


if __name__ == "__main__":
    main()
