from paramiko.config import SSHConfig
from paramiko.auth_strategy import AuthStrategy
from invoke.executor import Executor
from invoke.runners import Runner
from invoke.config import (
    Config as InvokeConfig,
    DataProxy as InvokeDataProxy,
)

from .connection import ConnectKwargs, Gateway

from os import PathLike
from typing_extensions import (
    Any,
    Literal, LiteralString,
    TypedDict,
    IO
)

#from .runners import Remote, RemoteShell
#from .util import get_local_user, debug

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
    
    run: InvokeConfigDefaultsRun
    runners: dict[str, Runner]
    sudo: InvokeConfigDefaultsSudo
    tasks: InvokeConfigDefaultsTasks
    timeouts: dict[str, float | None]

class InvokeConfigDefaultsRun(TypedDict):
    asynchronous: bool
    disown: bool
    dry: bool
    echo: bool
    echo_stdin: IO[str] | None
    encoding: str | None
    env: dict[str, str]
    err_stream: Any | None
    fallback: bool
    hide: LiteralString | Literal[False] | None
    in_stream: Any | None
    out_stream: Any | None
    echo_format: str
    pty: bool
    replace_env: bool
    shell: str
    warn: bool
    watchers: list[Any]

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
    run: InvokeConfigDefaultsRun
    runners: dict[str, Runner]
    sudo: InvokeConfigDefaultsSudo
    tasks: InvokeConfigDefaultsTasks
    timeouts: dict[str, float | None]


class _FabricConfigNamespace:
    authentication: FabricConfigDefaultsAuth
    connect_kwargs: ConnectKwargs
    forward_agent: bool
    gateway: Gateway | None
    inline_ssh_env: bool
    load_ssh_configs: bool
    port: str
    ssh_config_path: PathLike[str] | None


class FabricConfigDefaultsAuth(TypedDict):
    identities: list[tuple[str | None, str | None, int | None]]
    strategy_class: type[AuthStrategy]

class FabricConfigDefaults(InvokeConfig):
    authentication: FabricConfigDefaultsAuth
    connect_kwargs: ConnectKwargs
    forward_agent: bool
    gateway: Gateway | None
    inline_ssh_env: bool
    load_ssh_configs: bool
    port: str
    ssh_config_path: PathLike[str] | None


class Config(InvokeConfig, _InvokeConfigNamespace, _FabricConfigNamespace):
    """
    An `invoke.config.Config` subclass with extra Fabric-related behavior.

    This class behaves like `invoke.config.Config` in every way, with the
    following exceptions:

    - its `global_defaults` staticmethod has been extended to add/modify some
      default settings (see its documentation, below, for details);
    - it triggers loading of Fabric-specific env vars (e.g.
      ``FABRIC_RUN_HIDE=true`` instead of ``INVOKE_RUN_HIDE=true``) and
      filenames (e.g. ``/etc/fabric.yaml`` instead of ``/etc/invoke.yaml``).
    - it extends the API to account for loading ``ssh_config`` files (which are
      stored as additional attributes and have no direct relation to the
      regular config data/hierarchy.)
    - it adds a new optional constructor, `from_v1`, which :ref:`generates
      configuration data from Fabric 1 <from-v1>`.

    Intended for use with `.Connection`, as using vanilla
    `invoke.config.Config` objects would require users to manually define
    ``port``, ``user`` and so forth.

    .. seealso:: :doc:`/concepts/configuration`, :ref:`ssh-config`

    .. versionadded:: 2.0
    """
    
    prefix: str
    
    
    base_ssh_config: SSHConfig
    
    _runtime_ssh_path: PathLike[str | bytes] | None
    _system_ssh_path: PathLike[str | bytes]
    _user_ssh_path: PathLike[str | bytes]
    
    _given_explicit_object: bool
    
    
    @classmethod
    def from_v1(cls, env, **kwargs) -> Config:
        """
        Alternate constructor which uses Fabric 1's ``env`` dict for settings.

        All keyword arguments besides ``env`` are passed unmolested into the
        primary constructor, with the exception of ``overrides``, which is used
        internally & will end up resembling the data from ``env`` with the
        user-supplied overrides on top.

        .. warning::
            Because your own config overrides will win over data from ``env``,
            make sure you only set values you *intend* to change from your v1
            environment!

        For details on exactly which ``env`` vars are imported and what they
        become in the new API, please see :ref:`v1-env-var-imports`.

        :param env:
            An explicit Fabric 1 ``env`` dict (technically, any
            ``fabric.utils._AttributeDict`` instance should work) to pull
            configuration from.

        .. versionadded:: 2.4
        """
        ...
    
    def __init__(self, *args, **kwargs) -> None:
        """
        Creates a new Fabric-specific config object.

        For most API details, see `invoke.config.Config.__init__`. Parameters
        new to this subclass are listed below.

        :param ssh_config:
            Custom/explicit `paramiko.config.SSHConfig` object. If given,
            prevents loading of any SSH config files. Default: ``None``.

        :param str runtime_ssh_path:
            Runtime SSH config path to load. Prevents loading of system/user
            files if given. Default: ``None``.

        :param str system_ssh_path:
            Location of the system-level SSH config file. Default:
            ``/etc/ssh/ssh_config``.

        :param str user_ssh_path:
            Location of the user-level SSH config file. Default:
            ``~/.ssh/config``.

        :param bool lazy:
            Has the same meaning as the parent class' ``lazy``, but
            additionally controls whether SSH config file loading is deferred
            (requires manually calling `load_ssh_config` sometime.) For
            example, one may need to wait for user input before calling
            `set_runtime_ssh_path`, which will inform exactly what
            `load_ssh_config` does.
        """
        ...
    
    def set_runtime_ssh_path(self, path: PathLike[str | bytes]) -> None:
        """
        Configure a runtime-level SSH config file path.

        If set, this will cause `load_ssh_config` to skip system and user
        files, as OpenSSH does.

        .. versionadded:: 2.0
        """
        ...
    
    def load_ssh_config(self) -> None:
        """
        Load SSH config file(s) from disk.

        Also (beforehand) ensures that Invoke-level config re: runtime SSH
        config file paths, is accounted for.

        .. versionadded:: 2.0
        """
        ...
    
    def clone(self, *args, **kwargs) -> Config: ...
    
    def _clone_init_kwargs(self, *args, **kw) -> dict[str, Any]: ...
    
    def _load_ssh_files(self) -> None:
        """
        Trigger loading of configured SSH config file paths.

        Expects that ``base_ssh_config`` has already been set to an
        `~paramiko.config.SSHConfig` object.

        :returns: ``None``.
        """
        ...
    
    def _load_ssh_file(self, path: PathLike[str | bytes]) -> None:
        """
        Attempt to open and parse an SSH config file at ``path``.

        Does nothing if ``path`` is not a path to a valid file.

        :returns: ``None``.
        """
        ...
    
    @staticmethod
    def global_defaults() -> FabricConfigDefaults:
        """
        Default configuration values and behavior toggles.

        Fabric only extends this method in order to make minor adjustments and
        additions to Invoke's `~invoke.config.Config.global_defaults`; see its
        documentation for the base values, such as the config subtrees
        controlling behavior of ``run`` or how ``tasks`` behave.

        For Fabric-specific modifications and additions to the Invoke-level
        defaults, see our own config docs at :ref:`default-values`.

        .. versionadded:: 2.0
        .. versionchanged:: 3.1
            Added the ``authentication`` settings section, plus sub-attributes
            such as ``authentication.strategy_class``.
        """
        ...
