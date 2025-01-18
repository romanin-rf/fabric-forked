from ._version import __version_info__, __version__
from .config import Config
from .connection import Connection
from .runners import Remote, RemoteShell, Result
from .group import Group, SerialGroup, ThreadingGroup, GroupResult
from .tasks import task, Task
from .executor import Executor

__all__ = [
    'Config',
    'Connection',
    'Remote', 'RemoteShell', 'Result',
    'Group', 'SerialGroup', 'ThreadingGroup', 'GroupResult',
    'task', 'Task',
    'Executor'
]

try:
    from .auth import OpenSSHAuthStrategy
    __all__.append( 'OpenSSHAuthStrategy' )
except ImportError:
    pass