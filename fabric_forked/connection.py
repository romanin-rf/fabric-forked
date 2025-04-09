
from paramiko import Channel
from paramiko.client import SSHClient
from paramiko.sftp_client import SFTPClient
from paramiko.config import SSHConfig
from paramiko.transport import Transport
from paramiko.agent import AgentRequestHandler

from invoke.runners import Runner

from .fabric.connection import Connection as FabricConnection
from .fabric.config import Config
from .fabric.runners import Remote, Result

from ._typing import Gateway, ConnectKwargs, RunKwargs, SudoRunKwargs, DictHost, AttributeDict, ShellKwargs

from os import PathLike
from contextlib import _GeneratorContextManager
from typing_extensions import Any, Literal, Unpack, IO, Self, overload

class Connection:
    @overload
    def __init__(self,
        host: str,
        user: str | None = None,
        port: int | None = None,
        config: Config | None = None,
        gateway: str | Gateway | Literal[False] | None = None,
        forward_agent: bool | None = None,
        connect_timeout: float | None = None,
        connect_kwargs: ConnectKwargs | None = None,
        inline_ssh_env: bool | None = None
    ) -> None:
        ...
    
    @overload
    def __init__(self, connection: FabricConnection) -> None: ...
    
    def __init__(
        self,
        host: str | FabricConnection,
        user: str | None = None,
        port: int | None = None,
        config: Config | None = None,
        gateway: str | Gateway | Literal[False] | None = None,
        forward_agent: bool | None = None,
        connect_timeout: float | None = None,
        connect_kwargs: ConnectKwargs | None = None,
        inline_ssh_env: bool | None = None
    ) -> None:
        if not isinstance(host, FabricConnection):
            self.__connection = FabricConnection(
                host=host, user=user, port=port,
                config=config,
                gateway=gateway, forward_agent=forward_agent,
                connect_timeout=connect_timeout, connect_kwargs=connect_kwargs,
                inline_ssh_env=inline_ssh_env,
            )
        else:
            self.__connection = host
    
    @classmethod
    def from_v1(cls, env: AttributeDict, **kwargs: Any) -> Self:
        return cls(FabricConnection.from_v1(env, **kwargs))
    
    # ^ Dunder Methods
    
    def __str__(self) -> str:
        return self.__connection.__repr__()
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __hash__(self) -> int:
        return hash(self._identity())
    
    def __eq__(self, other: Self | Any) -> bool:
        if not isinstance(other, Connection):
            return False
        return self._identity() == other._identity()
    
    def __lt__(self, other: Self | Any) -> bool:
        if not isinstance(other, Connection):
            return False
        return self._identity() < other._identity()
    
    def __enter__(self) -> Self:
        return self
    
    def __exit__(self, *args: type[BaseException] | Exception) -> None:
        self.close()
    
    # ^ Public Propertyes
    
    @property
    def cwd(self) -> PathLike[str]:
        return self.__connection.cwd
    
    @property
    def host(self) -> str:
        return self.__connection.host
    
    @property
    def original_host(self) -> str | None:
        return self.__connection.original_host
    
    @property
    def user(self) -> str | None:
        return self.__connection.user
    
    @property
    def port(self) -> int | None:
        return self.__connection.port
    
    @property
    def gateway(self) -> str | Gateway | None:
        return self.__connection.gateway
    
    @property
    def is_connected(self) -> bool:
        return self.__connection.is_connected
    
    @property
    def client(self) -> SSHClient:
        return self.__connection.client
    
    @property
    def ssh_config(self) -> SSHConfig:
        return self.__connection.ssh_config
    
    @property
    def transport(self) -> Transport:
        return self.__connection.transport
    
    @property
    def command_cwds(self) -> list[str]:
        return self.__connection.command_cwds
    
    @property
    def command_prefixes(self) -> list[str]:
        return self.__connection.command_prefixes
    
    @property
    def forward_agent(self) -> bool:
        return bool(self.__connection.forward_agent)
    
    @property
    def connect_timeout(self) -> int:
        return self.__connection.connect_timeout
    
    # ^ Hidden Propertyes
    
    @property
    def _sftp(self) -> SFTPClient:
        return self.__connection._sftp
    
    @property
    def _agent_handler(self) -> AgentRequestHandler | None:
        return self.__connection._agent_handler
    
    @property
    def _proxies(self) -> tuple[str, ...]:
        return self.__connection._proxies
    
    @property
    def _is_root(self) -> bool:
        return self.__connection._is_root
    
    @property
    def _is_leaf(self) -> bool:
        return self.__connection._is_leaf
    
    # ^ Hidden Methods
    
    def _track_removal_of(self, key: str) -> None:
        self.__connection._track_removal_of(key)
    
    def _track_modification_of(self, key: str, value: str) -> None:
        self.__connection._track_modification_of(key, value)
    
    def _set(self, *args, **kwargs) -> None:
        self.__connection._set(*args, **kwargs)
    
    def _get(self, key: str) -> Any:
        return self.__connection._get(key)
    
    def _identity(self) -> tuple[str, str | None, int | None]:
        return self.__connection._identity()
    
    def _remote_runner(self) -> Remote:
        return self.__connection._remote_runner()
    
    def _prefix_commands(self, commands: str) -> str:
        return self.__connection._prefix_commands(commands)
    
    def _run(self, runner: Runner, command: str, **kwargs: Unpack[RunKwargs]) -> Result | None:
        return self.__connection._run(runner, command, **kwargs)
    
    def _sudo(self, runner: Runner, command: str, **kwargs: Unpack[SudoRunKwargs]) -> Result | None:
        return self.__connection._sudo(runner, command, **kwargs)
    
    # ^ Public Methods
    
    def resolve_connect_kwargs(self, connect_kwargs: ConnectKwargs) -> dict[str, Any | dict[str, Any]]:
        return self.__connection.resolve_connect_kwargs(connect_kwargs)
    
    def derive_shorthand(self, host_string: str) -> DictHost:
        return self.__connection.derive_shorthand(host_string)
    
    def sftp(self) -> SFTPClient:
        return self.__connection.sftp()
    
    def create_channel(self) -> Channel:
        return self.__connection.create_session()
    
    def get_gateway(self) -> str | Gateway | None:
        return self.__connection.get_gateway()
    
    def run(self, command: str, **kwargs: Unpack[RunKwargs]) -> Result | None:
        return self.__connection.run(command, **kwargs)
    
    def sudo(self, command: str, **kwargs: Unpack[SudoRunKwargs]) -> Result | None:
        return self.__connection.sudo(command, **kwargs)
    
    def shell(self, **kwargs: Unpack[ShellKwargs]) -> Result | None:
        self.__connection.local
        return self.__connection.shell(**kwargs)
    
    def local(self, *args: Any, **kwargs: Unpack[RunKwargs]) -> Result | None:
        return self.__connection.local(*args, **kwargs)
    
    def cd(self, path: PathLike | str) -> _GeneratorContextManager[None]:
        return self.__connection.cd(path)
    
    def forward_local(self,
        local_port: int,
        remote_port: int | None = None,
        remote_host: str = "localhost",
        local_host: str = "localhost"
    ) -> _GeneratorContextManager:
        return self.__connection.forward_local(local_port, remote_port, remote_host, local_host)
    
    def forward_remote(self,
        remote_port: int,
        local_port: int | None = None,
        remote_host: str = "127.0.0.1",
        local_host: str = "localhost"
    ) -> _GeneratorContextManager:
        return self.__connection.forward_remote(remote_port, local_port, remote_host, local_host)
    
    def open(self) -> None:
        self.__connection.open()
    
    def open_gateway(self) -> Gateway:
        return self.__connection.open_gateway()
    
    def get(self, *args, **kwargs):
        self.__connection.get()

    def put(self,
        local: PathLike[str | bytes] | IO[str | bytes],
        remote: PathLike[str | bytes] | None = None,
        preserve_mode: bool = True
    ) -> Result:
        return self.__connection.put(local, remote, preserve_mode)
    
    def get(self,
        remote: PathLike[str | bytes],
        local: PathLike[str | bytes] | IO[str | bytes] | None = None,
        preserve_mode: bool = True
    ) -> Result:
        return self.__connection.get(remote, local, preserve_mode)
    
    def close(self) -> None:
        self.__connection.close()
    
    # ^ DataProxy Methods
    
    def clear(self) -> None:
        self.__connection.clear()
    
    def update(self, *args, **kwargs) -> None:
        self.__connection.update(*args, **kwargs)