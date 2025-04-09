import copy
import errno
import os

from invoke.config import Config as InvokeConfig, merge_dicts
from paramiko.config import SSHConfig

from .runners import Remote, RemoteShell
from .util import get_local_user, debug


class Config(InvokeConfig):
    prefix = "fabric"

    @classmethod
    def from_v1(cls, env, **kwargs):
        data = kwargs.pop("overrides", {})
        for subdict in ("connect_kwargs", "run", "sudo", "timeouts"):
            data.setdefault(subdict, {})
        data["run"].setdefault("pty", env.always_use_pty)
        data.setdefault("gateway", env.gateway)
        data.setdefault("forward_agent", env.forward_agent)
        if env.key_filename is not None:
            data["connect_kwargs"].setdefault("key_filename", env.key_filename)
        data["connect_kwargs"].setdefault("allow_agent", not env.no_agent)
        data.setdefault("ssh_config_path", env.ssh_config_path)
        data["sudo"].setdefault("password", env.sudo_password)
        passwd = env.password
        data["connect_kwargs"].setdefault("password", passwd)
        if not data["sudo"]["password"]:
            data["sudo"]["password"] = passwd
        data["sudo"].setdefault("prompt", env.sudo_prompt)
        data["timeouts"].setdefault("connect", env.timeout)
        data.setdefault("load_ssh_configs", env.use_ssh_config)
        data["run"].setdefault("warn", env.warn_only)
        kwargs["overrides"] = data
        return cls(**kwargs)

    def __init__(self, *args, **kwargs):
        ssh_config = kwargs.pop("ssh_config", None)
        lazy = kwargs.get("lazy", False)
        self.set_runtime_ssh_path(kwargs.pop("runtime_ssh_path", None))
        system_path = kwargs.pop("system_ssh_path", "/etc/ssh/ssh_config")
        self._set(_system_ssh_path=system_path)
        self._set(_user_ssh_path=kwargs.pop("user_ssh_path", "~/.ssh/config"))
        explicit = ssh_config is not None
        self._set(_given_explicit_object=explicit)
        if ssh_config is None:
            ssh_config = SSHConfig()
        self._set(base_ssh_config=ssh_config)
        super().__init__(*args, **kwargs)
        if not lazy:
            self.load_ssh_config()

    def set_runtime_ssh_path(self, path):
        self._set(_runtime_ssh_path=path)

    def load_ssh_config(self):
        if self.ssh_config_path:
            self._runtime_ssh_path = self.ssh_config_path
        if not self._given_explicit_object:
            self._load_ssh_files()

    def clone(self, *args, **kwargs):
        new = super().clone(*args, **kwargs)
        for attr in (
            "_runtime_ssh_path",
            "_system_ssh_path",
            "_user_ssh_path",
        ):
            setattr(new, attr, getattr(self, attr))
        self.load_ssh_config()
        return new

    def _clone_init_kwargs(self, *args, **kw):
        kwargs = super()._clone_init_kwargs(*args, **kw)
        new_config = SSHConfig()
        new_config._config = copy.deepcopy(self.base_ssh_config._config)
        return dict(kwargs, ssh_config=new_config)

    def _load_ssh_files(self):
        if self._runtime_ssh_path is not None:
            path = self._runtime_ssh_path
            if not os.path.exists(path):
                raise FileNotFoundError(
                    errno.ENOENT, "No such file or directory", path
                )
            self._load_ssh_file(os.path.expanduser(path))
        elif self.load_ssh_configs:
            for path in (self._user_ssh_path, self._system_ssh_path):
                self._load_ssh_file(os.path.expanduser(path))

    def _load_ssh_file(self, path):
        if os.path.isfile(path):
            old_rules = len(self.base_ssh_config._config)
            with open(path) as fd:
                self.base_ssh_config.parse(fd)
            new_rules = len(self.base_ssh_config._config)
            msg = "Loaded {} new ssh_config rules from {!r}"
            debug(msg.format(new_rules - old_rules, path))
        else:
            debug("File not found, skipping")

    @staticmethod
    def global_defaults():
        defaults = InvokeConfig.global_defaults()
        ours = {
            "authentication": {
                "identities": [],
                "strategy_class": None,
            },
            "connect_kwargs": {},
            "forward_agent": False,
            "gateway": None,
            "inline_ssh_env": True,
            "load_ssh_configs": True,
            "port": 22,
            "runners": {"remote": Remote, "remote_shell": RemoteShell},
            "ssh_config_path": None,
            "tasks": {"collection_name": "fabfile"},
            "timeouts": {"connect": None},
            "user": get_local_user(),
        }
        merge_dicts(defaults, ours)
        return defaults
