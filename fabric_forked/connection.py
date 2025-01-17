from contextlib import contextmanager
from io import StringIO
from threading import Event
import socket

from decorator import decorator
from invoke import Context
from invoke.exceptions import ThreadException
from paramiko.agent import AgentRequestHandler
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.config import SSHConfig
from paramiko.proxy import ProxyCommand

from .config import Config
from .exceptions import InvalidV1Env
from .transfer import Transfer
from .tunnels import TunnelManager, Tunnel


@decorator
def opens(method, self, *args, **kwargs):
    self.open()
    return method(self, *args, **kwargs)


def derive_shorthand(host_string: str):
    user_hostport = host_string.rsplit("@", 1)
    hostport = user_hostport.pop()
    user = user_hostport[0] if user_hostport and user_hostport[0] else None
    if hostport.count(":") > 1:
        host = hostport
        port = None
    else:
        host_port = hostport.rsplit(":", 1)
        host = host_port.pop(0) or None
        port = host_port[0] if host_port and host_port[0] else None
    if port is not None:
        port = int(port)
    return {"user": user, "host": host, "port": port}


class Connection(Context):
    host = None
    original_host = None
    user = None
    port = None
    ssh_config = None
    gateway = None
    forward_agent = None
    connect_timeout = None
    connect_kwargs = None
    client = None
    transport = None
    _sftp = None
    _agent_handler = None

    @classmethod
    def from_v1(cls, env, **kwargs):
        if not env.host_string:
            raise InvalidV1Env(
                "Supplied v1 env has an empty `host_string` value! Please make sure you're calling Connection.from_v1 within a connected Fabric 1 session."  # noqa
            )
        connect_kwargs = kwargs.setdefault("connect_kwargs", {})
        kwargs.setdefault("host", env.host_string)
        shorthand = derive_shorthand(env.host_string)
        kwargs.setdefault("user", env.user)
        if not shorthand["port"]:
            kwargs.setdefault("port", int(env.port))
        if env.key_filename is not None:
            connect_kwargs.setdefault("key_filename", env.key_filename)
        if "config" not in kwargs:
            kwargs["config"] = Config.from_v1(env)
        return cls(**kwargs)

    def __init__(
        self,
        host,
        user=None,
        port=None,
        config=None,
        gateway=None,
        forward_agent=None,
        connect_timeout=None,
        connect_kwargs=None,
        inline_ssh_env=None,
    ):
        super().__init__(config=config)
        if config is None:
            config = Config()
        elif not isinstance(config, Config):
            config = config.clone(into=Config)
        self._set(_config=config)
        shorthand = self.derive_shorthand(host)
        host = shorthand["host"]
        err = "You supplied the {} via both shorthand and kwarg! Please pick one."  # noqa
        if shorthand["user"] is not None:
            if user is not None:
                raise ValueError(err.format("user"))
            user = shorthand["user"]
        if shorthand["port"] is not None:
            if port is not None:
                raise ValueError(err.format("port"))
            port = shorthand["port"]
        self.ssh_config = self.config.base_ssh_config.lookup(host)
        self.original_host = host
        self.host = host
        if "hostname" in self.ssh_config:
            self.host = self.ssh_config["hostname"]
        self.port = port or int(self.ssh_config.get("port", self.config.port))
        self.gateway = gateway if gateway is not None else self.get_gateway()
        if forward_agent is None:
            forward_agent = self.config.forward_agent
            if "forwardagent" in self.ssh_config:
                map_ = {"yes": True, "no": False}
                forward_agent = map_[self.ssh_config["forwardagent"]]
        self.forward_agent = forward_agent

        if connect_timeout is None:
            connect_timeout = self.ssh_config.get(
                "connecttimeout", self.config.timeouts.connect
            )
        if connect_timeout is not None:
            connect_timeout = int(connect_timeout)
        self.connect_timeout = connect_timeout
        self.connect_kwargs = self.resolve_connect_kwargs(connect_kwargs)
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        self.client = client
        self.transport = None
        if inline_ssh_env is None:
            inline_ssh_env = self.config.inline_ssh_env
        self.inline_ssh_env = inline_ssh_env

    def resolve_connect_kwargs(self, connect_kwargs):
        constructor_kwargs = connect_kwargs or {}
        config_kwargs = self.config.connect_kwargs
        constructor_keys = constructor_kwargs.get("key_filename", [])
        config_keys = config_kwargs.get("key_filename", [])
        ssh_config_keys = self.ssh_config.get("identityfile", [])
        final_kwargs = constructor_kwargs or config_kwargs
        final_keys = []
        for value in (config_keys, constructor_keys, ssh_config_keys):
            if isinstance(value, str):
                value = [value]
            final_keys.extend(value)
        if final_keys:
            final_kwargs["key_filename"] = final_keys

        return final_kwargs

    def get_gateway(self):
        if "proxyjump" in self.ssh_config:
            hops = reversed(self.ssh_config["proxyjump"].split(","))
            prev_gw = None
            for hop in hops:
                if self.derive_shorthand(hop)["host"] == self.host:
                    return None
                kwargs = dict(config=self.config.clone())
                if prev_gw is not None:
                    kwargs["gateway"] = prev_gw
                cxn = Connection(hop, **kwargs)
                prev_gw = cxn
            return prev_gw
        elif "proxycommand" in self.ssh_config:
            return self.ssh_config["proxycommand"]
        return self.config.gateway

    def __repr__(self):
        bits = [("host", self.host)]
        if self.user != self.config.user:
            bits.append(("user", self.user))
        if self.port != self.config.port:
            bits.append(("port", self.port))
        if self.gateway:
            val = "proxyjump"
            if isinstance(self.gateway, str):
                val = "proxycommand"
            bits.append(("gw", val))
        return "<Connection {}>".format(
            " ".join("{}={}".format(*x) for x in bits)
        )

    def _identity(self):
        return (self.host, self.user, self.port)

    def __eq__(self, other):
        if not isinstance(other, Connection):
            return False
        return self._identity() == other._identity()

    def __lt__(self, other):
        return self._identity() < other._identity()

    def __hash__(self):
        return hash(self._identity())

    def derive_shorthand(self, host_string):
        return derive_shorthand(host_string)

    @property
    def is_connected(self):
        return self.transport.active if self.transport else False

    def open(self):
        if self.is_connected:
            return
        err = "Refusing to be ambiguous: connect() kwarg '{}' was given both via regular arg and via connect_kwargs!"  # noqa
        for key in """
            hostname
            port
            username
        """.split():
            if key in self.connect_kwargs:
                raise ValueError(err.format(key))
        if (
            "timeout" in self.connect_kwargs
            and self.connect_timeout is not None
        ):
            raise ValueError(err.format("timeout"))
        kwargs = dict(
            self.connect_kwargs,
            username=self.user,
            hostname=self.host,
            port=self.port,
        )
        if self.gateway:
            kwargs["sock"] = self.open_gateway()
        if self.connect_timeout:
            kwargs["timeout"] = self.connect_timeout
        if "key_filename" in kwargs and not kwargs["key_filename"]:
            del kwargs["key_filename"]
        auth_strategy_class = self.authentication.strategy_class
        if auth_strategy_class is not None:
            for key in (
                "allow_agent",
                "key_filename",
                "look_for_keys",
                "passphrase",
                "password",
                "pkey",
                "username",
            ):
                kwargs.pop(key, None)

            kwargs["auth_strategy"] = auth_strategy_class(
                ssh_config=self.ssh_config,
                fabric_config=self.config,
                username=self.user,
            )
        # Actually connect!
        result = self.client.connect(**kwargs)
        self.transport = self.client.get_transport()
        return result

    def open_gateway(self):
        if isinstance(self.gateway, str):
            ssh_conf = SSHConfig()
            dummy = "Host {}\n    ProxyCommand {}"
            ssh_conf.parse(StringIO(dummy.format(self.host, self.gateway)))
            return ProxyCommand(ssh_conf.lookup(self.host)["proxycommand"])
        self.gateway.open()
        return self.gateway.transport.open_channel(
            kind="direct-tcpip",
            dest_addr=(self.host, int(self.port)),
            src_addr=("", 0),
        )

    def close(self):
        if self._sftp is not None:
            self._sftp.close()
            self._sftp = None

        if self.is_connected:
            self.client.close()
            if self.forward_agent and self._agent_handler is not None:
                self._agent_handler.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @opens
    def create_session(self):
        channel = self.transport.open_session()
        if self.forward_agent:
            self._agent_handler = AgentRequestHandler(channel)
        return channel

    def _remote_runner(self):
        return self.config.runners.remote(
            context=self, inline_env=self.inline_ssh_env
        )

    @opens
    def run(self, command, **kwargs):
        return self._run(self._remote_runner(), command, **kwargs)

    @opens
    def sudo(self, command, **kwargs):
        return self._sudo(self._remote_runner(), command, **kwargs)

    @opens
    def shell(self, **kwargs):
        runner = self.config.runners.remote_shell(context=self)
        allowed = ("encoding", "env", "in_stream", "replace_env", "watchers")
        new_kwargs = {}
        for key, value in self.config.global_defaults()["run"].items():
            if key in allowed:
                new_kwargs[key] = kwargs.pop(key, self.config.run[key])
            else:
                new_kwargs[key] = value
        new_kwargs.update(pty=True)
        if kwargs:
            err = "shell() got unexpected keyword arguments: {!r}"
            raise TypeError(err.format(list(kwargs.keys())))
        return runner.run(command=None, **new_kwargs)

    def local(self, *args, **kwargs):
        return super().run(*args, **kwargs)

    @opens
    def sftp(self):
        if self._sftp is None:
            self._sftp = self.client.open_sftp()
        return self._sftp

    def get(self, *args, **kwargs):
        """
        Get a remote file to the local filesystem or file-like object.

        Simply a wrapper for `.Transfer.get`. Please see its documentation for
        all details.

        .. versionadded:: 2.0
        """
        return Transfer(self).get(*args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Put a local file (or file-like object) to the remote filesystem.

        Simply a wrapper for `.Transfer.put`. Please see its documentation for
        all details.

        .. versionadded:: 2.0
        """
        return Transfer(self).put(*args, **kwargs)
    
    @contextmanager
    @opens
    def forward_local(
        self,
        local_port,
        remote_port=None,
        remote_host="localhost",
        local_host="localhost",
    ):
        if not remote_port:
            remote_port = local_port
        finished = Event()
        manager = TunnelManager(
            local_port=local_port,
            local_host=local_host,
            remote_port=remote_port,
            remote_host=remote_host,
            transport=self.transport,
            finished=finished,
        )
        manager.start()
        try:
            yield
        finally:
            finished.set()
            manager.join()
            wrapper = manager.exception()
            if wrapper is not None:
                if wrapper.type is ThreadException:
                    raise wrapper.value
                else:
                    raise ThreadException([wrapper])

    @contextmanager
    @opens
    def forward_remote(
        self,
        remote_port,
        local_port=None,
        remote_host="127.0.0.1",
        local_host="localhost",
    ):
        if not local_port:
            local_port = remote_port
        tunnels = []
        def callback(channel, src_addr_tup, dst_addr_tup):
            sock = socket.socket()
            sock.connect((local_host, local_port))
            tunnel = Tunnel(channel=channel, sock=sock, finished=Event())
            tunnel.start()
            tunnels.append(tunnel)
        try:
            self.transport.request_port_forward(
                address=remote_host, port=remote_port, handler=callback
            )
            yield
        finally:
            for tunnel in tunnels:
                tunnel.finished.set()
                tunnel.join()
            self.transport.cancel_port_forward(
                address=remote_host, port=remote_port
            )
