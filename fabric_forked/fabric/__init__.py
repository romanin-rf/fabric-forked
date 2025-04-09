from ._version import __version_info__, __version__
from .connection import Connection
from .config import Config
from .runners import Remote, RemoteShell, Result
from .group import Group, SerialGroup, ThreadingGroup, GroupResult
from .tasks import task, Task
from .executor import Executor

__all__ = [
    '__version_info__', '__version__',
    'Connection',
    'Config',
    'Remote', 'RemoteShell', 'Result',
    'Group', 'SerialGroup', 'ThreadingGroup', 'GroupResult',
    'task', 'Task',
    'Executor'
]

try:
    from .auth import OpenSSHAuthStrategy
    __all__.append('OpenSSHAuthStrategy')
except ImportError:
    pass