from paramiko.config import SSHConfig
from invoke.config import Config as InvokeConfig

from ._types import (
    _InvokeConfigNamespace, _FabricConfigNamespace,
    FabricConfigDefaults
)

from os import PathLike
from typing_extensions import Any


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
