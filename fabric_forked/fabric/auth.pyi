from paramiko import Agent
from paramiko.config import SSHConfig
from paramiko.transport import Transport
from paramiko.auth_strategy import (
    AuthStrategy,
    Password,
    InMemoryPrivateKey,
    OnDiskPrivateKey,
    SourceResult
)

from .config import Config

from typing_extensions import Iterator


class OpenSSHAuthStrategy(AuthStrategy):
    """
    Auth strategy that tries very hard to act like the OpenSSH client.

    .. warning::
        As of version 3.1, this class is **EXPERIMENTAL** and **incomplete**.
        It works best with passphraseless (eg ssh-agent) private key auth for
        now and will grow more features in future releases.

    For example, it accepts a `~paramiko.config.SSHConfig` and uses any
    relevant ``IdentityFile`` directives from that object, along with keys from
    your home directory and any local SSH agent. Keys specified at runtime are
    tried last, just as with ``ssh -i /path/to/key`` (this is one departure
    from the legacy/off-spec auth behavior observed in older Paramiko and
    Fabric versions).

    We explicitly do not document the full details here, because the point is
    to match the documented/observed behavior of OpenSSH. Please see the `ssh
    <https://man.openbsd.org/ssh>`_ and `ssh_config
    <https://man.openbsd.org/ssh_config>`_ man pages for more information.

    .. versionadded:: 3.1
    """
    
    username: str
    config: Config
    agent: Agent
    
    def __init__(self, ssh_config: SSHConfig, fabric_config: Config, username: str) -> None:
        """
        Extends superclass with additional inputs.

        Specifically:

        - ``fabric_config``, a `fabric.Config` instance for the current
          session.
        - ``username``, which is unified by our intended caller so we don't
          have to - it's a synthesis of CLI, runtime,
          invoke/fabric-configuration, and ssh_config configuration.

        Also handles connecting to an SSH agent, if possible, for easier
        lifecycle tracking.
        """
        ...
    
    def get_pubkeys(self) -> Iterator[OnDiskPrivateKey | InMemoryPrivateKey]: ...
    
    def get_sources(self) -> Iterator[OnDiskPrivateKey | InMemoryPrivateKey | Password]: ...
    
    def authenticate(self, transport: Transport) -> list[SourceResult]: ...
    
    def close(self) -> None: ...