from invoke.executor import Executor
from invoke.runners import (
    Runner,
    Result as InvokeRunResult
)
from invoke.config import (
    Config as InvokeConfig,
    DataProxy as InvokeDataProxy,
)

from paramiko.pkey import PKey
from paramiko.transport import Transport
from paramiko.auth_strategy import AuthStrategy
from paramiko.channel import Channel
from paramiko.proxy import ProxyCommand

from .config import Config
from .connection import Connection
from .runners import Result as RunResult

from os import PathLike
from socket import SocketType
from contextlib import contextmanager
from typing_extensions import (
    Any,
    IO,
    Iterator, Generator,
    NamedTuple, TypedDict,
    Literal, LiteralString,
    Callable,
    TypeVar, TypeAlias, Unpack
)

# ! CONFIG TYPES

class _InvokeConfigNamespace:
    _proxies: tuple[str | LiteralString, ...]
    _keypath: tuple[str, ...]
    _root: InvokeDataProxy
    
    _config: dict[str, Any]
    _defaults: dict[str, Any]
    _file_suffixes: tuple[str, ...]
    _collection: dict[str, Any]
    _system_prefix: str | None
    _system_path: PathLike[str | bytes] | None
    _system_found: str | None
    _user_prefix: str
    _user_path: PathLike[str | bytes] | None
    _user_found: str | None
    _user: dict[str, Any]
    _project_prefix: str | None
    _project_path: PathLike[str | bytes] | None
    _project_found: str | None
    _project: dict[str, Any]
    _runtime_path: PathLike[str | bytes] | None
    _runtime: dict[str, Any]
    _runtime_found: str | None
    _env_prefix: str
    _env: dict[str, Any]
    _overrides: dict[str, Any]
    _modifications: dict[str, Any]
    _deletions: dict[str, Any]
    
    run: 'InvokeConfigDefaultsRun'
    runners: dict[str, Runner]
    sudo: 'InvokeConfigDefaultsSudo'
    tasks: 'InvokeConfigDefaultsTasks'
    timeouts: dict[str, float | None]

class InvokeConfigDefaultsRun(TypedDict):
    asynchronous: bool = False
    disown: bool = False
    dry: bool = False
    echo: bool = False
    echo_stdin: IO[str | bytes] | None = None
    encoding: str | None = None
    env: dict[str, str] = {}
    err_stream: Any | None = None
    fallback: bool = True
    hide: Literal['in', 'out'] | bool | None = None
    in_stream: Any | None = None
    out_stream: Any | None = None
    echo_format: str = "\033[1;37m{command}\033[0m"
    pty: bool = False
    replace_env: bool = False
    shell: str = ...
    warn: bool = False
    watchers: list[Any] = []

class InvokeConfigDefaultsSudo(TypedDict):
    password: str | None
    prompt: str
    user: str | None

class InvokeConfigDefaultsTasks(TypedDict):
    auto_dash_names: bool
    collection_name: str
    dedupe: bool
    executor_class: type[Executor] | None
    ignore_unknown_help: bool
    search_root: str | None

class InvokeConfigDefaults(TypedDict):
    run: 'InvokeConfigDefaultsRun'
    runners: dict[str, Runner]
    sudo: 'InvokeConfigDefaultsSudo'
    tasks: InvokeConfigDefaultsTasks
    timeouts: dict[str, float | None]


class _FabricConfigNamespace:
    authentication: 'FabricConfigDefaultsAuth'
    connect_kwargs: 'ConnectKwargs'
    forward_agent: bool
    gateway: 'Gateway' | None
    inline_ssh_env: bool
    load_ssh_configs: bool
    port: str
    ssh_config_path: PathLike[str] | None


class FabricConfigDefaultsAuth(TypedDict):
    identities: list[tuple[str | None, str | None, int | None]]
    strategy_class: type[AuthStrategy]

class FabricConfigDefaults(InvokeConfig):
    authentication: 'FabricConfigDefaultsAuth'
    connect_kwargs: 'ConnectKwargs'
    forward_agent: bool = False
    gateway: 'Gateway' | None = None
    inline_ssh_env: bool
    load_ssh_configs: bool
    port: str
    ssh_config_path: PathLike[str] | None

# ! CONNECTION TYPES

Gateway = Channel | ProxyCommand | Connection

RunKwargs: TypeAlias    = InvokeConfigDefaultsRun
SudoKwargs: TypeAlias   = InvokeConfigDefaultsSudo

class SudoRunKwargs(InvokeConfigDefaultsRun, InvokeConfigDefaultsSudo):
    pass

Result: TypeAlias       = RunResult | InvokeRunResult

ReturnType              = TypeVar('ReturnType')


class ShellKwargs(TypedDict):
    encoding: str | None
    env: dict[str | Any] | None
    in_stream: Any | None
    replace_env: bool
    watchers: list[Any]


class DictHost(TypedDict):
    host: str | None
    port: str | None
    user: str | None

class AttributeDict(NamedTuple):
    host_string: str | None
    key_filename: str | None
    port: str | None
    user: str | None

class ConnectKwargs(TypedDict):
    hostname: str
    port: int
    username: str
    password: str
    pkey: PKey
    key_filename: str
    timeout: float
    allow_agent: bool
    look_for_keys: bool
    compress: bool
    sock: SocketType
    gss_auth: bool
    gss_kex: bool
    gss_deleg_creds: bool
    gss_host: str
    banner_timeout: float
    auth_timeout: float
    channel_timeout: float
    gss_trust_dns: bool
    passphrase: str
    disabled_algorithms: dict[str, list[str]]
    transport_factory: Callable[..., Transport]
    auth_strategy: AuthStrategy


class ConnectionKwargs(TypedDict):
    host: str
    user: str | None
    port: int | None
    config: 'Config' | None
    gateway: str | 'Gateway' | Literal[False] | None
    forward_agent: bool | None
    connect_timeout: float | None
    connect_kwargs: 'ConnectKwargs' | None
    inline_ssh_env: bool | None

# ! Invoke Types

class DataProxy:
    _proxies: tuple[str, ...]

    @classmethod
    def from_data(cls, data: dict[str, Any], root: 'DataProxy' | None = None, keypath: tuple[str, ...] = tuple()) -> 'DataProxy': ...
    #def __getattr__(self, key: str) -> Unpack[DataProxy]: ...
    #def __setattr__(self, key: str, value: Any) -> None: ...
    #def __delattr__(self, name: str) -> None: ...
    def __setitem__(self, key: str, value: str) -> None: ...
    def __getitem__(self, key: str) -> Any: ...
    def __delitem__(self, key: str) -> None: ...
    def __iter__(self) -> Iterator[dict[str, Any]]: ...
    def __eq__(self, other: object) -> bool: ...
    def __len__(self) -> int: ...
    def __repr__(self) -> str: ...
    def __contains__(self, key: str) -> bool: ...

    @property
    def _is_leaf(self) -> bool: ...

    @property
    def _is_root(self) -> bool: ...
    
    def _get(self, key: str) -> Any: ...
    def _set(self, *args: Any, **kwargs: Any) -> None: ...
    def _track_removal_of(self, key: str) -> None: ...
    def _track_modification_of(self, key: str, value: str) -> None: ...
    def clear(self) -> None: ...
    def pop(self, *args: Any) -> Any: ...
    def popitem(self) -> Any: ...
    def setdefault(self, *args: Any) -> Any: ...
    def update(self, *args: Any, **kwargs: Any) -> None: ...


class Context(DataProxy):
    config: Config
    command_prefixes: list[str]
    command_cwds: list[str]
    
    def __init__(self, config: Config | None = None) -> None: ...

    @property
    def config(self) -> Config: ...

    @config.setter
    def config(self, value: Config) -> None: ...

    def run(self, command: str, **kwargs: Unpack[RunKwargs]) -> Result | None: ...
    def _run(self, runner: "Runner", command: str, **kwargs: Unpack[RunKwargs]) -> InvokeRunResult | None: ...

    def sudo(self, command: str, **kwargs: Unpack[SudoRunKwargs]) -> InvokeRunResult | None: ...
    def _sudo(
        self, runner: "Runner", command: str, **kwargs: Unpack[SudoRunKwargs]
    ) -> InvokeRunResult | None: ...

    def _prefix_commands(self, command: str) -> str: ...

    @contextmanager
    def prefix(self, command: str) -> Generator[None, None, None]: ...

    @property
    def cwd(self) -> str: ...

    @contextmanager
    def cd(self, path: PathLike | str) -> Generator[None, None, None]: ...