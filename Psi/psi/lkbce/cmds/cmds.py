import fcntl
import os
import re
import subprocess

import psi.utils


class Command:
    # All command line argument will be printed at separate line and they aren't empty strings. So one empty string
    # can safely separate different build commands from each other.
    cmds_separator = '\n'

    def __init__(self, argv):
        self.cmd = os.path.basename(argv[0])
        self.opts = argv[1:]

    def launch(self):
        with psi.utils.LockedOpen(os.environ['LINUX_KERNEL_RAW_BUILD_CMS_FILE'], 'a') as fp:
            fp.write('{0}\n{1}'.format('\n'.join([self.cmd.upper() if self.cmd != 'gcc' else 'CC'] + self.opts),
                                       self.cmds_separator))

        # Eclude path where wrapper build command is located.
        os.environ['PATH'] = re.sub(r'^[^:]+:', '', os.environ['PATH'])

        # Execute original build command.
        subprocess.call(tuple(['aspectator' if self.cmd == 'gcc' else self.cmd] + self.opts))
