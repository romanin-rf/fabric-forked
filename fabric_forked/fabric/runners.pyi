import signal

from paramiko.channel import Channel
from invoke import Runner, Result as InvokeResult

from .connection import Connection, RunKwargs

from typing_extensions import Any, Unpack, NoReturn

def cares_about_SIGWINCH() -> bool: ...


class Remote(Runner):
    """
    Run a shell command over an SSH connection.

    This class subclasses `invoke.runners.Runner`; please see its documentation
    for most public API details.

    .. note::
        `.Remote`'s ``__init__`` method expects a `.Connection` (or subclass)
        instance for its ``context`` argument.

    .. versionadded:: 2.0
    """
    
    inline_env: bool
    channel: Channel
    context: Connection
    
    def __init__(self, *args, **kwargs):
        """
        Thin wrapper for superclass' ``__init__``; please see it for details.

        Additional keyword arguments defined here are listed below.

        :param bool inline_env:
            Whether to 'inline' shell env vars as prefixed parameters, instead
            of trying to submit them via `.Channel.update_environment`.
            Default: ``True``.

        .. versionchanged:: 2.3
            Added the ``inline_env`` parameter.
        .. versionchanged:: 3.0
            Changed the default value of ``inline_env`` from ``False`` to
            ``True``.
        """
        ...
    
    def start(self,
        command: str,
        shell: Any,
        env: dict[str, Any],
        timeout: float | None = None
    ) -> None: ...

    def send_start_message(self, command: str) -> None: ...

    def run(self, command: str, **kwargs: Unpack[RunKwargs]) -> InvokeResult | None: ...

    def read_proc_stdout(self, num_bytes: int) -> bytes: ...

    def read_proc_stderr(self, num_bytes: int) -> bytes: ...

    def _write_proc_stdin(self, data: bytes | bytearray) -> None: ...

    def close_proc_stdin(self) -> None: ...

    @property
    def process_is_finished(self) -> bool: ...

    def send_interrupt(self, interrupt: InterruptedError) -> NoReturn | None: ...

    def returncode(self) -> int: ...

    def generate_result(self, **kwargs) -> Result: ...

    def stop(self) -> None: ...

    def kill(self) -> None: ...

    def handle_window_change(self, signum: signal._SIGNUM, frame) -> None:
        """
        Respond to a `signal.SIGWINCH` (as a standard signal handler).

        Sends a window resize command via Paramiko channel method.
        """
        ...


class RemoteShell(Remote):
    def send_start_message(self, command: str) -> None: ...


class Result(InvokeResult):
    """
    An `invoke.runners.Result` exposing which `.Connection` was run against.

    Exposes all attributes from its superclass, then adds a ``.connection``,
    which is simply a reference to the `.Connection` whose method yielded this
    result.

    .. versionadded:: 2.0
    """
    
    connection: Connection

    def __init__(self, **kwargs) -> None: ...
