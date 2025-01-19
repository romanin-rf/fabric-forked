from functools import partial
from getpass import getpass
from pathlib import Path

from paramiko import Agent, PKey
from paramiko.auth_strategy import (
    AuthStrategy,
    Password,
    InMemoryPrivateKey,
    OnDiskPrivateKey,
)

from .util import win32


class OpenSSHAuthStrategy(AuthStrategy):
    def __init__(self, ssh_config, fabric_config, username):
        super().__init__(ssh_config=ssh_config)
        self.username = username
        self.config = fabric_config
        self.agent = Agent()

    def get_pubkeys(self):
        config_certs, config_keys, cli_certs, cli_keys = [], [], [], []
        for path in self.config.authentication.identities:
            try:
                key = PKey.from_path(path)
            except FileNotFoundError:
                continue
            source = OnDiskPrivateKey(
                username=self.username,
                source="python-config",
                path=path,
                pkey=key,
            )
            (cli_certs if key.public_blob else cli_keys).append(source)
        for path in self.ssh_config.get("identityfile", []):
            try:
                key = PKey.from_path(path)
            except FileNotFoundError:
                continue
            source = OnDiskPrivateKey(
                username=self.username,
                source="ssh-config",
                path=path,
                pkey=key,
            )
            (config_certs if key.public_blob else config_keys).append(source)
        if not any((config_certs, config_keys, cli_certs, cli_keys)):
            user_ssh = Path.home() / f"{'' if win32 else '.'}ssh"
            for type_ in ("rsa", "ecdsa", "ed25519", "dsa"):
                path = user_ssh / f"id_{type_}"
                try:
                    key = PKey.from_path(path)
                except FileNotFoundError:
                    continue
                source = OnDiskPrivateKey(
                    username=self.username,
                    source="implicit-home",
                    path=path,
                    pkey=key,
                )
                dest = config_certs if key.public_blob else config_keys
                dest.append(source)
        agent_keys = self.agent.get_keys()
        for source in config_certs:
            yield source
        for source in cli_certs:
            yield source
        deferred_agent_keys = []
        for key in agent_keys:
            config_index = None
            for i, config_key in enumerate(config_keys):
                if config_key.pkey == key:
                    config_index = i
                    break
            if config_index:
                yield InMemoryPrivateKey(username=self.username, pkey=key)
                del config_keys[config_index]
            else:
                deferred_agent_keys.append(key)
        for key in deferred_agent_keys:
            yield InMemoryPrivateKey(username=self.username, pkey=key)
        for source in cli_keys:
            yield source
        for source in config_keys:
            yield source

    def get_sources(self):
        yield from self.get_pubkeys()
        user = self.username
        prompter = partial(getpass, f"{user}'s password: ")
        yield Password(username=self.username, password_getter=prompter)

    def authenticate(self, *args, **kwargs):
        try:
            return super().authenticate(*args, **kwargs)
        finally:
            self.close()

    def close(self):
        self.agent.close()
