from queue import Queue

from invoke.util import ExceptionHandlingThread

from .connection import Connection
from .exceptions import GroupException


class Group(list):
    def __init__(self, *hosts, **kwargs):
        self.extend([Connection(host, **kwargs) for host in hosts])

    @classmethod
    def from_connections(cls, connections):
        group = cls()
        group.extend(connections)
        return group

    def _do(self, method, *args, **kwargs):
        raise NotImplementedError

    def run(self, *args, **kwargs):
        return self._do("run", *args, **kwargs)

    def sudo(self, *args, **kwargs):
        return self._do("sudo", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._do("put", *args, **kwargs)

    def get(self, *args, **kwargs):
        if len(args) < 2 and "local" not in kwargs:
            kwargs["local"] = "{host}/"
        return self._do("get", *args, **kwargs)

    def close(self):
        for cxn in self:
            cxn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class SerialGroup(Group):
    def _do(self, method, *args, **kwargs):
        results = GroupResult()
        excepted = False
        for cxn in self:
            try:
                results[cxn] = getattr(cxn, method)(*args, **kwargs)
            except Exception as e:
                results[cxn] = e
                excepted = True
        if excepted:
            raise GroupException(results)
        return results


def thread_worker(cxn, queue, method, args, kwargs):
    result = getattr(cxn, method)(*args, **kwargs)
    queue.put((cxn, result))


class ThreadingGroup(Group):
    def _do(self, method, *args, **kwargs):
        results = GroupResult()
        queue = Queue()
        threads = []
        for cxn in self:
            thread = ExceptionHandlingThread(
                target=thread_worker,
                kwargs=dict(
                    cxn=cxn,
                    queue=queue,
                    method=method,
                    args=args,
                    kwargs=kwargs,
                ),
            )
            threads.append(thread)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        while not queue.empty():
            cxn, result = queue.get(block=False)
            results[cxn] = result
        excepted = False
        for thread in threads:
            wrapper = thread.exception()
            if wrapper is not None:
                cxn = wrapper.kwargs["kwargs"]["cxn"]
                results[cxn] = wrapper.value
                excepted = True
        if excepted:
            raise GroupException(results)
        return results


class GroupResult(dict):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._successes = {}
        self._failures = {}

    def _bifurcate(self):
        if self._successes or self._failures:
            return
        for key, value in self.items():
            if isinstance(value, BaseException):
                self._failures[key] = value
            else:
                self._successes[key] = value

    @property
    def succeeded(self):
        self._bifurcate()
        return self._successes

    @property
    def failed(self):
        self._bifurcate()
        return self._failures
