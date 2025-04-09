import os
import posixpath
import stat

from pathlib import Path

from .util import debug


class Transfer:
    def __init__(self, connection):
        self.connection = connection

    @property
    def sftp(self):
        return self.connection.sftp()

    def is_remote_dir(self, path):
        try:
            return stat.S_ISDIR(self.sftp.stat(path).st_mode)
        except IOError:
            return False

    def get(self, remote, local=None, preserve_mode=True):
        if not remote:
            raise ValueError("Remote path must not be empty!")
        orig_remote = remote
        remote = posixpath.join(
            self.sftp.getcwd() or self.sftp.normalize("."), remote
        )
        orig_local = local
        is_file_like = hasattr(local, "write") and callable(local.write)
        remote_filename = posixpath.basename(remote)
        if not local:
            local = remote_filename
        if not is_file_like:
            local = local.format(
                host=self.connection.host,
                user=self.connection.user,
                port=self.connection.port,
                dirname=posixpath.dirname(remote),
                basename=remote_filename,
            )
            if local.endswith(os.sep):
                dir_path = local
                local = os.path.join(local, remote_filename)
            else:
                dir_path, _ = os.path.split(local)
            local = os.path.abspath(local)
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        if is_file_like:
            self.sftp.getfo(remotepath=remote, fl=local)
        else:
            self.sftp.get(remotepath=remote, localpath=local)
            if preserve_mode:
                remote_mode = self.sftp.stat(remote).st_mode
                mode = stat.S_IMODE(remote_mode)
                os.chmod(local, mode)
        return Result(
            orig_remote=orig_remote,
            remote=remote,
            orig_local=orig_local,
            local=local,
            connection=self.connection,
        )

    def put(self, local, remote=None, preserve_mode=True):
        if not local:
            raise ValueError("Local path must not be empty!")
        is_file_like = hasattr(local, "write") and callable(local.write)
        orig_remote = remote
        if is_file_like:
            local_base = getattr(local, "name", None)
        else:
            local_base = os.path.basename(local)
        if not remote:
            if is_file_like:
                raise ValueError(
                    "Must give non-empty remote path when local is a file-like object!"  # noqa
                )
            else:
                remote = local_base
                debug("Massaged empty remote path into {!r}".format(remote))
        elif self.is_remote_dir(remote):
            if local_base:
                remote = posixpath.join(remote, local_base)
            else:
                if is_file_like:
                    raise ValueError(
                        "Can't put a file-like-object into a directory unless it has a non-empty .name attribute!"  # noqa
                    )
                else:
                    raise ValueError(
                        "Somehow got an empty local file basename ({!r}) when uploading to a directory ({!r})!".format(  # noqa
                            local_base, remote
                        )
                    )
        prejoined_remote = remote
        remote = posixpath.join(
            self.sftp.getcwd() or self.sftp.normalize("."), remote
        )
        if remote != prejoined_remote:
            msg = "Massaged relative remote path {!r} into {!r}"
            debug(msg.format(prejoined_remote, remote))
        orig_local = local
        if not is_file_like:
            local = os.path.abspath(local)
            if local != orig_local:
                debug(
                    "Massaged relative local path {!r} into {!r}".format(
                        orig_local, local
                    )
                )  # noqa
        if is_file_like:
            msg = "Uploading file-like object {!r} to {!r}"
            debug(msg.format(local, remote))
            pointer = local.tell()
            try:
                local.seek(0)
                self.sftp.putfo(fl=local, remotepath=remote)
            finally:
                local.seek(pointer)
        else:
            debug("Uploading {!r} to {!r}".format(local, remote))
            self.sftp.put(localpath=local, remotepath=remote)
            if preserve_mode:
                local_mode = os.stat(local).st_mode
                mode = stat.S_IMODE(local_mode)
                self.sftp.chmod(remote, mode)
        return Result(
            orig_remote=orig_remote,
            remote=remote,
            orig_local=orig_local,
            local=local,
            connection=self.connection,
        )


class Result:
    def __init__(self, local, orig_local, remote, orig_remote, connection):
        self.local = local
        self.orig_local = orig_local
        self.remote = remote
        self.orig_remote = orig_remote
        self.connection = connection
