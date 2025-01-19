"""
CLI entrypoint & parser configuration.

Builds on top of Invoke's core functionality for same.
"""

import getpass
from pathlib import Path

from invoke import Argument, Collection, Exit, Program
from invoke import __version__ as invoke
from paramiko import __version__ as paramiko, Agent

from . import __version__ as fabric
from . import Config, Executor


class Fab(Program):
    def print_version(self):
        super().print_version()
        print("Paramiko {}".format(paramiko))
        print("Invoke {}".format(invoke))

    def core_args(self):
        core_args = super().core_args()
        my_args = [
            Argument(
                names=("H", "hosts"),
                help="Comma-separated host name(s) to execute tasks against.",
            ),
            Argument(
                names=("i", "identity"),
                kind=list,
                help="Path to runtime SSH identity (key) file. May be given multiple times.",  # noqa
            ),
            Argument(
                names=("list-agent-keys",),
                kind=bool,
                help="Display ssh-agent key list, and exit.",
            ),
            Argument(
                names=("prompt-for-login-password",),
                kind=bool,
                help="Request an upfront SSH-auth password prompt.",
            ),
            Argument(
                names=("prompt-for-passphrase",),
                kind=bool,
                help="Request an upfront SSH key passphrase prompt.",
            ),
            Argument(
                names=("S", "ssh-config"),
                help="Path to runtime SSH config file.",
            ),
            Argument(
                names=("t", "connect-timeout"),
                kind=int,
                help="Specifies default connection timeout, in seconds.",
            ),
        ]
        return core_args + my_args

    @property
    def _remainder_only(self):
        return (
            not self.core.unparsed
            and self.core.remainder
            and not self.args.complete.value
        )

    def load_collection(self):
        if self._remainder_only:
            self.collection = Collection()
        else:
            super().load_collection()

    def no_tasks_given(self):
        if not self._remainder_only:
            super().no_tasks_given()

    def create_config(self):
        self.config = self.config_class(lazy=True)
        self.config.load_base_conf_files()
        self.config.merge()

    def update_config(self):
        super().update_config(merge=False)
        self.config.set_runtime_ssh_path(self.args["ssh-config"].value)
        self.config.load_ssh_config()
        connect_kwargs = {}
        paths = self.args["identity"].value
        if paths:
            connect_kwargs["key_filename"] = paths
            self.config._overrides["authentication"] = dict(
                identities=[Path(x) for x in paths]
            )
        timeout = self.args["connect-timeout"].value
        if timeout:
            connect_kwargs["timeout"] = timeout
        if self.args["prompt-for-login-password"].value:
            prompt = "Enter login password for use with SSH auth: "
            connect_kwargs["password"] = getpass.getpass(prompt)
        if self.args["prompt-for-passphrase"].value:
            prompt = "Enter passphrase for use unlocking SSH keys: "
            connect_kwargs["passphrase"] = getpass.getpass(prompt)
        self.config._overrides["connect_kwargs"] = connect_kwargs
        self.config.merge()
    
    def parse_core(self, *args, **kwargs):
        super().parse_core(*args, **kwargs)
        if self.args["list-agent-keys"].value:
            keys = Agent().get_keys()
            for key in keys:
                tpl = "{} {} {} ({})"
                print(
                    tpl.format(
                        key.get_bits(),
                        key.fingerprint,
                        key.comment,
                        key.algorithm_name,
                    )
                )
            raise Exit


def make_program():
    return Fab(
        name="Fabric",
        version=fabric,
        executor_class=Executor,
        config_class=Config,
    )


program = make_program()
