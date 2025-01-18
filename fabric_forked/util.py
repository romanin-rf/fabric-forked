import logging
import sys


log = logging.getLogger("fabric")
for x in ("debug",):
    globals()[x] = getattr(log, x)


win32 = sys.platform == "win32"


def get_local_user() -> str | None:
    """
    Return the local executing username, or ``None`` if one can't be found.

    .. versionadded:: 2.0
    """
    import getpass
    username = None
    try:
        username = getpass.getuser()
    except KeyError:
        pass
    except ImportError:  # pragma: nocover
        if win32:
            import win32api # type: ignore
            import win32security  # noqa # type: ignore
            import win32profile  # noqa # type: ignore
            username = win32api.GetUserName()
    return username
