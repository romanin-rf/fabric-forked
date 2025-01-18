import select
import socket
import time
from threading import Event

from invoke.exceptions import ThreadException
from invoke.util import ExceptionHandlingThread


class TunnelManager(ExceptionHandlingThread):
    def __init__(
        self,
        local_host,
        local_port,
        remote_host,
        remote_port,
        transport,
        finished,
    ):
        super().__init__()
        self.local_address = (local_host, local_port)
        self.remote_address = (remote_host, remote_port)
        self.transport = transport
        self.finished = finished

    def _run(self):
        tunnels = []
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        sock.bind(self.local_address)
        sock.listen(1)
        while not self.finished.is_set():
            try:
                tun_sock, local_addr = sock.accept()
                tun_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except BlockingIOError:
                time.sleep(0.01)
                continue
            channel = self.transport.open_channel(
                "direct-tcpip", self.remote_address, local_addr
            )
            finished = Event()
            tunnel = Tunnel(channel=channel, sock=tun_sock, finished=finished)
            tunnel.start()
            tunnels.append(tunnel)
        exceptions = []
        for tunnel in tunnels:
            tunnel.finished.set()
            tunnel.join()
            wrapper = tunnel.exception()
            if wrapper:
                exceptions.append(wrapper)
        if exceptions:
            raise ThreadException(exceptions)
        sock.close()


class Tunnel(ExceptionHandlingThread):
    def __init__(self, channel, sock, finished):
        self.channel = channel
        self.sock = sock
        self.finished = finished
        self.socket_chunk_size = 1024
        self.channel_chunk_size = 1024
        super().__init__()

    def _run(self):
        try:
            empty_sock, empty_chan = None, None
            while not self.finished.is_set():
                r, w, x = select.select([self.sock, self.channel], [], [], 1)
                if self.sock in r:
                    empty_sock = self.read_and_write(
                        self.sock, self.channel, self.socket_chunk_size
                    )
                if self.channel in r:
                    empty_chan = self.read_and_write(
                        self.channel, self.sock, self.channel_chunk_size
                    )
                if empty_sock or empty_chan:
                    break
        finally:
            self.channel.close()
            self.sock.close()

    def read_and_write(self, reader, writer, chunk_size):
        data = reader.recv(chunk_size)
        if len(data) == 0:
            return True
        writer.sendall(data)
