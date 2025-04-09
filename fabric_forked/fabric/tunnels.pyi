"""
Tunnel and connection forwarding internals.

If you're looking for simple, end-user-focused connection forwarding, please
see `.Connection`, e.g. `.Connection.forward_local`.
"""

import socket
from threading import Event

from paramiko import Transport, Channel
from invoke.util import ExceptionHandlingThread

from typing_extensions import Literal


class TunnelManager(ExceptionHandlingThread):
    """
    Thread subclass for tunnelling connections over SSH between two endpoints.

    Specifically, one instance of this class is sufficient to sit around
    forwarding any number of individual connections made to one end of the
    tunnel or the other. If you need to forward connections between more than
    one set of ports, you'll end up instantiating multiple TunnelManagers.

    Wraps a `~paramiko.transport.Transport`, which should already be connected
    to the remote server.

    .. versionadded:: 2.0
    """
    
    local_address: tuple[str, int]
    remote_address: tuple[str, int]
    transport: Transport
    finished: Event

    def __init__(self,
        local_host: str,
        local_port: int,
        remote_host: str,
        remote_port: int,
        transport: Transport,
        finished: Event,
    ) -> None:
        ...

    def _run(self) -> None: ...


class Tunnel(ExceptionHandlingThread):
    """
    Bidirectionally forward data between an SSH channel and local socket.

    .. versionadded:: 2.0
    """
    
    channel: Channel
    sock: socket.SocketType
    finished: Event
    socket_chunk_size: int
    channel_chunk_size: int

    def __init__(self, channel: Channel, sock: socket.SocketType, finished: Event) -> None: ...

    def _run(self) -> None: ...

    def read_and_write(self, reader: socket.SocketType, writer: socket.SocketType, chunk_size) -> Literal[True] | None:
        """
        Read ``chunk_size`` from ``reader``, writing result to ``writer``.

        Returns ``None`` if successful, or ``True`` if the read was empty.

        .. versionadded:: 2.0
        """
        ...
