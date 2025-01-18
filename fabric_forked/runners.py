import signal
import threading

from invoke import Runner, pty_size, Result as InvokeResult


def cares_about_SIGWINCH():
    return (
        hasattr(signal, "SIGWINCH")
        and threading.current_thread() is threading.main_thread()
    )


class Remote(Runner):
    def __init__(self, *args, **kwargs):
        self.inline_env = kwargs.pop("inline_env", None)
        super().__init__(*args, **kwargs)

    def start(self, command, shell, env, timeout=None):
        self.channel = self.context.create_session()
        if self.using_pty:
            cols, rows = pty_size()
            self.channel.get_pty(width=cols, height=rows)
            if cares_about_SIGWINCH():
                signal.signal(signal.SIGWINCH, self.handle_window_change)
        if env:
            if self.inline_env:
                parameters = " ".join(
                    ["{}={}".format(k, v) for k, v in sorted(env.items())]
                )
                command = "export {} && {}".format(parameters, command)
            else:
                self.channel.update_environment(env)
        self.send_start_message(command)

    def send_start_message(self, command):
        self.channel.exec_command(command)

    def run(self, command, **kwargs):
        kwargs.setdefault("replace_env", True)
        return super().run(command, **kwargs)

    def read_proc_stdout(self, num_bytes):
        return self.channel.recv(num_bytes)

    def read_proc_stderr(self, num_bytes):
        return self.channel.recv_stderr(num_bytes)

    def _write_proc_stdin(self, data):
        return self.channel.sendall(data)

    def close_proc_stdin(self):
        return self.channel.shutdown_write()

    @property
    def process_is_finished(self):
        return self.channel.exit_status_ready()

    def send_interrupt(self, interrupt):
        if self.using_pty:
            self.channel.send("\x03")
        else:
            raise interrupt

    def returncode(self):
        return self.channel.recv_exit_status()

    def generate_result(self, **kwargs):
        kwargs["connection"] = self.context
        return Result(**kwargs)

    def stop(self):
        super().stop()
        if hasattr(self, "channel"):
            self.channel.close()
        if cares_about_SIGWINCH():
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)

    def kill(self):
        self.channel.close()

    def handle_window_change(self, signum, frame):
        self.channel.resize_pty(*pty_size())


class RemoteShell(Remote):
    def send_start_message(self, command):
        self.channel.invoke_shell()


class Result(InvokeResult):
    def __init__(self, **kwargs):
        connection = kwargs.pop("connection")
        super().__init__(**kwargs)
        self.connection = connection
