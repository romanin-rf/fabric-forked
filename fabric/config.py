import copy
import errno
import os

from invoke.config import Config as InvokeConfig, merge_dicts
from paramiko.config import SSHConfig

from .util import get_local_user, debug


class Config(InvokeConfig):
    """
    An `invoke.config.Config` subclass with extra Fabric-related behavior.

    This class behaves like `invoke.config.Config` in every way, with the
    following exceptions:

    - its `global_defaults` staticmethod has been extended to add/modify some
      default settings (see its documentation, below, for details);
    - it accepts additional instantiation arguments related to loading
      ``ssh_config`` files.

    Intended for use with `.Connection`, as using vanilla
    `invoke.config.Config` objects would require users to manually define
    ``port``, ``user`` and so forth.

    .. seealso:: :doc:`/concepts/configuration`, :ref:`ssh-config`
    """
    def __init__(self, *args, **kwargs):
        """
        Creates a new Fabric-specific config object.

        For most API details, see `invoke.config.Config.__init__`. Parameters
        new to this subclass are listed below.

        :param ssh_config:
            Custom/explicit `paramiko.config.SSHConfig` object. If given,
            prevents loading of any SSH config files. Default: ``None``.

        :param str runtime_ssh_path:
            Runtime SSH config path to load. Prevents loading of system/user
            files if given. Default: ``None``.

        :param str system_ssh_path:
            Location of the system-level SSH config file. Default:
            ``/etc/ssh/ssh_config``.

        :param str user_ssh_path:
            Location of the user-level SSH config file. Default:
            ``~/.ssh/config``.
        """
        # Tease out our own kwargs.
        # TODO: consider moving more stuff out of __init__ and into methods so
        # there's less of this sort of splat-args + pop thing? Eh.
        ssh_config = kwargs.pop('ssh_config', None)
        self._set(_runtime_ssh_path=kwargs.pop('runtime_ssh_path', None))
        system_path = kwargs.pop('system_ssh_path', '/etc/ssh/ssh_config')
        self._set(_system_ssh_path=system_path)
        self._set(_user_ssh_path=kwargs.pop('user_ssh_path', '~/.ssh/config'))

        # Record whether we were given an explicit object (so other steps know
        # whether to bother loading from disk or not)
        # This needs doing before super __init__ as that calls our post_init
        explicit = ssh_config is not None
        self._set(_given_explicit_object=explicit)

        # Arrive at some non-None SSHConfig object (upon which to run .parse()
        # later, in _load_ssh_file())
        if ssh_config is None:
            ssh_config = SSHConfig()
        self._set(base_ssh_config=ssh_config)

        # Now that our own attributes have been prepared, we can fall up into
        # parent __init__(), which will trigger post_init() (which needs the
        # attributes we just set up)
        super(Config, self).__init__(*args, **kwargs)

    def post_init(self):
        super(Config, self).post_init()
        # Now that regular config is loaded, we can update the runtime SSH
        # config path
        if self.ssh_config_path:
            self._runtime_ssh_path = self.ssh_config_path
        # Load files from disk, if necessary
        if not self._given_explicit_object:
            self.load_ssh_files()

    def clone(self, *args, **kwargs):
        # TODO: clone() at this point kinda-sorta feels like it's retreading
        # __reduce__ and the related (un)pickling stuff...
        # Get cloned obj.
        # NOTE: Because we also extend .init_kwargs, the actual core SSHConfig
        # data is passed in at init time (ensuring no files get loaded a 2nd,
        # etc time) and will already be present, so we don't need to set
        # .base_ssh_config ourselves. Similarly, there's no need to worry about
        # how the SSH config paths may be inaccurate until below; nothing will
        # be referencing them.
        new = super(Config, self).clone(*args, **kwargs)
        # Copy over our custom attributes, so that the clone still resembles us
        # re: recording where the data originally came from (in case anything
        # re-runs .load_ssh_files(), for example).
        for attr in (
            '_runtime_ssh_path',
            '_system_ssh_path',
            '_user_ssh_path',
        ):
            setattr(new, attr, getattr(self, attr))
        # All done
        return new

    def _clone_init_kwargs(self, *args, **kw):
        # Parent kwargs
        kwargs = super(Config, self)._clone_init_kwargs(*args, **kw)
        # Transmit our internal SSHConfig via explicit-obj kwarg, thus
        # bypassing any file loading. (Our extension of clone() above copies
        # over other attributes as well so that the end result looks consistent
        # with reality.)
        new_config = SSHConfig()
        # TODO: as with other spots, this implies SSHConfig needs a cleaner
        # public API re: creating and updating its core data.
        new_config._config = copy.deepcopy(self.base_ssh_config._config)
        return dict(
            kwargs,
            ssh_config=new_config,
        )

    def load_ssh_files(self):
        """
        Trigger loading of configured SSH config file paths.

        Expects that `base_ssh_config` has already been set to an `SSHConfig`
        object.

        :returns: ``None``.
        """
        if self._runtime_ssh_path is not None:
            path = self._runtime_ssh_path
            # Manually blow up like open() (_load_ssh_file normally doesn't)
            if not os.path.exists(path):
                msg = "No such file or directory: {!r}".format(path)
                raise IOError(errno.ENOENT, msg)
            self._load_ssh_file(os.path.expanduser(path))
        elif self.load_ssh_configs:
            for path in (self._user_ssh_path, self._system_ssh_path):
                self._load_ssh_file(os.path.expanduser(path))

    def _load_ssh_file(self, path):
        """
        Attempt to open and parse an SSH config file at ``path``.

        Does nothing if ``path`` is not a path to a valid file.

        :returns: ``None``.
        """
        if os.path.isfile(path):
            old_rules = len(self.base_ssh_config._config)
            with open(path) as fd:
                self.base_ssh_config.parse(fd)
            new_rules = len(self.base_ssh_config._config)
            msg = "Loaded {0} new ssh_config rules from {1!r}"
            debug(msg.format(new_rules - old_rules, path))
        else:
            debug("File not found, skipping")

    @staticmethod
    def global_defaults():
        """
        Default configuration values and behavior toggles.

        Fabric only extends this method in order to make minor adjustments and
        additions to Invoke's `~invoke.config.Config.global_defaults`; see its
        documentation for the base values, such as the config subtrees
        controlling behavior of ``run`` or how ``tasks`` behave.

        For Fabric-specific modifications and additions to the Invoke-level
        defaults, see our own config docs at :ref:`default-values`.
        """
        # TODO: is it worth moving all of our 'new' settings to a discrete
        # namespace for cleanliness' sake? e.g. ssh.port, ssh.user etc.
        # It wouldn't actually simplify this code any, but it would make it
        # easier for users to determine what came from which library/repo.
        defaults = InvokeConfig.global_defaults()
        ours = {
            # New settings
            'port': 22,
            'user': get_local_user(),
            'forward_agent': False,
            'gateway': None,
            'load_ssh_configs': True,
            'connect_kwargs': {},
            # TODO: this becomes an override once Invoke grows execution
            # timeouts (which should be timeouts.execute)
            'timeouts': {
                'connect': None,
            },
            'ssh_config_path': None,
            # Overrides of existing settings
            'run': {
                'replace_env': True,
            },
        }
        merge_dicts(defaults, ours)
        return defaults
