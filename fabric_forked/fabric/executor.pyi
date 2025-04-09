import invoke
from invoke import Call, Task

from .tasks import ConnectionCall

from typing_extensions import Any, Iterable


class Executor(invoke.Executor):
    """
    `~invoke.executor.Executor` subclass which understands Fabric concepts.

    Designed to work in tandem with Fabric's `@task
    <fabric.tasks.task>`/`~fabric.tasks.Task`, and is capable of acting on
    information stored on the resulting objects -- such as default host lists.

    This class is written to be backwards compatible with vanilla Invoke-level
    tasks, which it simply delegates to its superclass.

    Please see the parent class' `documentation <invoke.executor.Executor>` for
    details on most public API members and object lifecycle.
    """
    
    def normalize_hosts(self, hosts: Iterable[str | dict[str, str]]) -> list[dict[str, str]]:
        """
        Normalize mixed host-strings-or-kwarg-dicts into kwarg dicts only.

        In other words, transforms data taken from the CLI (--hosts, always
        strings) or decorator arguments (may be strings or kwarg dicts) into
        kwargs suitable for creating Connection instances.

        Subclasses may wish to override or extend this to perform, for example,
        database or custom config file lookups (vs this default behavior, which
        is to simply assume that strings are 'host' kwargs).

        :param hosts:
            Potentially heterogenous list of host connection values, as per the
            ``hosts`` param to `.task`.

        :returns: Homogenous list of Connection init kwarg dicts.
        """
        ...
    
    def expand_calls(self, 
        calls: Iterable[ConnectionCall | Call | Task],
        apply_hosts: bool = True
    ) -> list[ConnectionCall]: ...
    
    def parameterize(self, call: Call, connection_init_kwargs: dict[str, Any]) -> ConnectionCall:
        """
        Parameterize a Call with its Context set to a per-host Connection.

        :param call:
            The generic `.Call` being parameterized.
        :param connection_init_kwargs:
            The dict of `.Connection` init params/kwargs to attach to the
            resulting `.ConnectionCall`.

        :returns:
            `.ConnectionCall`.
        """
        ...
    
    def dedupe(self, tasks: Iterable[Task]) -> list[Task]: ...