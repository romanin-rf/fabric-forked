from .fabric._version import __version_info__, __version__
from .connection import Connection
from .fabric.config import Config
from .fabric.runners import Remote, RemoteShell, Result
from .fabric.group import Group, SerialGroup, ThreadingGroup, GroupResult
from .fabric.tasks import task, Task
from .fabric.executor import Executor


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
    from .fabric.auth import OpenSSHAuthStrategy
    __all__.append('OpenSSHAuthStrategy')
except ImportError:
    pass