import invoke

from .config import Config
from .connection import Connection, ConnectionKwargs

from typing_extensions import Any, Callable


class Task(invoke.Task):
    """
    Extends `invoke.tasks.Task` with knowledge of target hosts and similar.

    As `invoke.tasks.Task` relegates documentation responsibility to its `@task
    <invoke.tasks.task>` expression, so we relegate most details to our version
    of `@task <fabric.tasks.task>` - please see its docs for details.

    .. versionadded:: 2.1
    """
    
    hosts: list[str | ConnectionKwargs]

    def __init__(self, *args, **kwargs) -> None: ...


def task(*args, **kwargs) -> Callable[..., Any]:
    """
    Wraps/extends Invoke's `@task <invoke.tasks.task>` with extra kwargs.

    See `the Invoke-level API docs <invoke.tasks.task>` for most details; this
    Fabric-specific implementation adds the following additional keyword
    arguments:

    :param hosts:
        An iterable of host-connection specifiers appropriate for eventually
        instantiating a `.Connection`. The existence of this argument will
        trigger automatic parameterization of the task when invoked from the
        CLI, similar to the behavior of :option:`--hosts`.

        .. note::
            This parameterization is "lower-level" than that driven by
            :option:`--hosts`: if a task decorated with this parameter is
            executed in a session where :option:`--hosts` was given, the
            CLI-driven value will win out.

        List members may be one of:

        - A string appropriate for being the first positional argument to
          `.Connection` - see its docs for details, but these are typically
          shorthand-only convenience strings like ``hostname.example.com`` or
          ``user@host:port``.
        - A dictionary appropriate for use as keyword arguments when
          instantiating a `.Connection`. Useful for values that don't mesh well
          with simple strings (e.g. statically defined IPv6 addresses) or to
          bake in more complex info (eg ``connect_timeout``, ``connect_kwargs``
          params like auth info, etc).

        These two value types *may* be mixed together in the same list, though
        we recommend that you keep things homogenous when possible, to avoid
        confusion when debugging.

        .. note::
            No automatic deduplication of values is performed; if you pass in
            multiple references to the same effective target host, the wrapped
            task will execute on that host multiple times (including making
            separate connections).

    .. versionadded:: 2.1
    """
    ...


class ConnectionCall(invoke.Call):
    """
    Subclass of `invoke.tasks.Call` that generates `Connections <.Connection>`.
    """
    
    init_kwargs: ConnectionKwargs

    def __init__(self, *args, **kwargs) -> None:
        """
        Creates a new `.ConnectionCall`.

        Performs minor extensions to `~invoke.tasks.Call` -- see its docstring
        for most details. Only specific-to-subclass params are documented here.

        :param dict init_kwargs:
            Keyword arguments used to create a new `.Connection` when the
            wrapped task is executed. Default: ``None``.
        """
        ...
    
    def __repr__(self) -> str: ...

    def clone_kwargs(self) -> dict[str, Any | ConnectionKwargs]: ...

    def make_context(self, config: Config) -> Connection: ...