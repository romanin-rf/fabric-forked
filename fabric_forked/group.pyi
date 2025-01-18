from queue import Queue

from .connection import Connection, ConnectKwargs
from .exceptions import NotImplementedWarning

from typing_extensions import (
    Any,
    Iterable,
    Self,
    TypeVar,
    Never,
    deprecated
)

DT = TypeVar('DT')


class Group(list[Connection]):
    """
    A collection of `.Connection` objects whose API operates on its contents.

    .. warning::
        **This is a partially abstract class**; you need to use one of its
        concrete subclasses (such as `.SerialGroup` or `.ThreadingGroup`) or
        you'll get ``NotImplementedError`` on most of the methods.

    Most methods in this class wrap those of `.Connection` and will accept the
    same arguments; however their return values and exception-raising behavior
    differ:

    - Return values are dict-like objects (`.GroupResult`) mapping
      `.Connection` objects to the return value for the respective connections:
      `.Group.run` returns a map of `.Connection` to `.runners.Result`,
      `.Group.get` returns a map of `.Connection` to `.transfer.Result`, etc.
    - If any connections encountered exceptions, a `.GroupException` is raised,
      which is a thin wrapper around what would otherwise have been the
      `.GroupResult` returned; within that wrapped `.GroupResult`, the
      excepting connections map to the exception that was raised, in place of a
      ``Result`` (as no ``Result`` was obtained.) Any non-excepting connections
      will have a ``Result`` value, as normal.

    For example, when no exceptions occur, a session might look like this::

        >>> group = SerialGroup('host1', 'host2')
        >>> group.run("this is fine")
        {
            <Connection host='host1'>: <Result cmd='this is fine' exited=0>,
            <Connection host='host2'>: <Result cmd='this is fine' exited=0>,
        }

    With exceptions (anywhere from 1 to "all of them"), it looks like so; note
    the different exception classes, e.g. `~invoke.exceptions.UnexpectedExit`
    for a completed session whose command exited poorly, versus
    `socket.gaierror` for a host that had DNS problems::

        >>> group = SerialGroup('host1', 'host2', 'notahost')
        >>> group.run("will it blend?")
        {
            <Connection host='host1'>: <Result cmd='will it blend?' exited=0>,
            <Connection host='host2'>: <UnexpectedExit: cmd='...' exited=1>,
            <Connection host='notahost'>: gaierror(...),
        }

    As with `.Connection`, `.Group` objects may be used as context managers,
    which will automatically `.close` the object on block exit.

    .. versionadded:: 2.0
    .. versionchanged:: 2.4
        Added context manager behavior.
    """
    
    def __init__(self, *hosts: str, **kwargs: ConnectKwargs) -> None:
        """
        Create a group of connections from one or more shorthand host strings.

        See `.Connection` for details on the format of these strings - they
        will be used as the first positional argument of `.Connection`
        constructors.

        Any keyword arguments given will be forwarded directly to those
        `.Connection` constructors as well. For example, to get a serially
        executing group object that connects to ``admin@host1``,
        ``admin@host2`` and ``admin@host3``, and forwards your SSH agent too::

            group = SerialGroup(
                "host1", "host2", "host3", user="admin", forward_agent=True,
            )

        .. versionchanged:: 2.3
            Added ``**kwargs`` (was previously only ``*hosts``).
        """
        ...
    
    @classmethod
    def from_connections(cls, connections: Iterable[Connection]) -> Group[Connection]:
        """
        Alternate constructor accepting `.Connection` objects.

        .. versionadded:: 2.0
        """
        ...
    
    @deprecated('This method is not implemented', category=NotImplementedWarning)
    def _do(self, method: str, *args, **kwargs) -> Never: ...
    
    def run(self, *args, **kwargs):
        """
        Executes `.Connection.run` on all member `Connections <.Connection>`.

        :returns: a `.GroupResult`.

        .. versionadded:: 2.0
        """
        ...
    
    def sudo(self, *args, **kwargs) -> GroupResult:
        """
        Executes `.Connection.sudo` on all member `Connections <.Connection>`.

        :returns: a `.GroupResult`.

        .. versionadded:: 2.6
        """
        ...
    
    def put(self, *args, **kwargs) -> GroupResult:
        """
        Executes `.Connection.put` on all member `Connections <.Connection>`.

        This is a straightforward application: aside from whatever the concrete
        group subclass does for concurrency or lack thereof, the effective
        result is like running a loop over the connections and calling their
        ``put`` method.

        :returns:
            a `.GroupResult` whose values are `.transfer.Result` instances.

        .. versionadded:: 2.6
        """
        ...
    
    def get(self, *args, **kwargs) -> GroupResult:
        """
        Executes `.Connection.get` on all member `Connections <.Connection>`.

        .. note::
            This method changes some behaviors over e.g. directly calling
            `.Connection.get` on a ``for`` loop of connections; the biggest is
            that the implied default value for the ``local`` parameter is
            ``"{host}/"``, which triggers use of local path parameterization
            based on each connection's target hostname.

            Thus, unless you override ``local`` yourself, a copy of the
            downloaded file will be stored in (relative) directories named
            after each host in the group.

        .. warning::
            Using file-like objects as the ``local`` argument is not currently
            supported, as it would be equivalent to supplying that same object
            to a series of individual ``get()`` calls.

        :returns:
            a `.GroupResult` whose values are `.transfer.Result` instances.

        .. versionadded:: 2.6
        """
        ...
    
    def close(self) -> None:
        """
        Executes `.Connection.close` on all member `Connections <.Connection>`.

        .. versionadded:: 2.4
        """
        ...
    
    def __enter__(self) -> Self: ...
    
    def __exit__(self, *exc) -> None: ...


class SerialGroup(Group):
    """
    Subclass of `.Group` which executes in simple, serial fashion.

    .. versionadded:: 2.0
    """

    def _do(self, method: str, *args, **kwargs) -> GroupResult: ...


def thread_worker(
    cxn: Connection,
    queue: Queue[tuple[Connection, Any]],
    method: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any]
) -> None: ...


class ThreadingGroup(Group):
    """
    Subclass of `.Group` which uses threading to execute concurrently.

    .. versionadded:: 2.0
    """

    def _do(self, method: str, *args, **kwargs) -> GroupResult: ...


class GroupResult(dict[Connection, DT | BaseException]):
    """
    Collection of results and/or exceptions arising from `.Group` methods.

    Acts like a dict, but adds a couple convenience methods, to wit:

    - Keys are the individual `.Connection` objects from within the `.Group`.
    - Values are either return values / results from the called method (e.g.
      `.runners.Result` objects), *or* an exception object, if one prevented
      the method from returning.
    - Subclasses `dict`, so has all dict methods.
    - Has `.succeeded` and `.failed` attributes containing sub-dicts limited to
      just those key/value pairs that succeeded or encountered exceptions,
      respectively.

      - Of note, these attributes allow high level logic, e.g. ``if
        mygroup.run('command').failed`` and so forth.

    .. versionadded:: 2.0
    """

    _successes: dict[Connection, DT]
    _failures: dict[Connection, BaseException]
    
    def __init__(self, *args, **kwargs) -> None: ...

    def _bifurcate(self) -> None: ...

    @property
    def succeeded(self) -> dict[Connection, DT]:
        """
        A sub-dict containing only successful results.

        .. versionadded:: 2.0
        """
        ...

    @property
    def failed(self) -> dict[Connection, BaseException]:
        """
        A sub-dict containing only failed results.

        .. versionadded:: 2.0
        """
        ...
