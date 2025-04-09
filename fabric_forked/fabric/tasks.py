import invoke

from .connection import Connection


class Task(invoke.Task):
    def __init__(self, *args, **kwargs):
        self.hosts = kwargs.pop("hosts", None)
        super().__init__(*args, **kwargs)


def task(*args, **kwargs):
    kwargs.setdefault("klass", Task)
    return invoke.task(*args, **kwargs)


class ConnectionCall(invoke.Call):
    def __init__(self, *args, **kwargs):
        init_kwargs = kwargs.pop("init_kwargs")
        super().__init__(*args, **kwargs)
        self.init_kwargs = init_kwargs

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs["init_kwargs"] = self.init_kwargs
        return kwargs

    def make_context(self, config):
        kwargs = self.init_kwargs
        kwargs["config"] = config
        return Connection(**kwargs)

    def __repr__(self):
        ret = super().__repr__()
        if self.init_kwargs:
            ret = ret[:-1] + ", host='{}'>".format(self.init_kwargs["host"])
        return ret
