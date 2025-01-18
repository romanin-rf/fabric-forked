import invoke
from invoke import Call, Task

from .tasks import ConnectionCall
from .exceptions import NothingToDo
from .util import debug


class Executor(invoke.Executor):
    def normalize_hosts(self, hosts):
        dicts = []
        for value in hosts or []:
            if not isinstance(value, dict):
                value = dict(host=value)
            dicts.append(value)
        return dicts

    def expand_calls(self, calls, apply_hosts=True):
        # Generate new call list with per-host variants & Connections inserted
        ret = []
        cli_hosts = []
        host_str = self.core[0].args.hosts.value
        if apply_hosts and host_str:
            cli_hosts = host_str.split(",")
        for call in calls:
            if isinstance(call, Task):
                call = Call(task=call)
            ret.extend(self.expand_calls(call.pre, apply_hosts=False))
            call_hosts = getattr(call, "hosts", None)
            cxn_params = self.normalize_hosts(cli_hosts or call_hosts)
            for init_kwargs in cxn_params:
                ret.append(self.parameterize(call, init_kwargs))
            if not cxn_params:
                ret.append(call)
            ret.extend(self.expand_calls(call.post, apply_hosts=False))
        if self.core.remainder:
            if not cli_hosts:
                raise NothingToDo(
                    "Was told to run a command, but not given any hosts to run it on!"  # noqa
                )
            def anonymous(c):
                c.run(self.core.remainder)
            anon = Call(Task(body=anonymous))
            for init_kwargs in self.normalize_hosts(cli_hosts):
                ret.append(self.parameterize(anon, init_kwargs))
        return ret

    def parameterize(self, call, connection_init_kwargs):
        msg = "Parameterizing {!r} with Connection kwargs {!r}"
        debug(msg.format(call, connection_init_kwargs))
        new_call_kwargs = dict(init_kwargs=connection_init_kwargs)
        clone = call.clone(into=ConnectionCall, with_=new_call_kwargs)
        return clone

    def dedupe(self, tasks):
        return tasks
