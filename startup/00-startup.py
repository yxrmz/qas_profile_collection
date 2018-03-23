import nslsii

nslsii.configure_base(get_ipython().user_ns, 'qas', bec=False)


# At the end of every run, verify that files were saved and
# print a confirmation message.
from bluesky.callbacks.broker import verify_files_saved
# RE.subscribe(post_run(verify_files_saved), 'stop')

# Optional: set any metadata that rarely changes.
RE.md['group'] = 'qas'
RE.md['beamline_id'] = 'QAS'
RE.md['proposal_id'] = None
# isstools reads these
RE.md['PI'] = "No PI"
RE.md['PROPOSAL'] = None
RE.md['SAF'] = None
RE.md['year'] = 2018
RE.md['cycle'] = 1
RE.is_aborted = False


# convenience imports
from bluesky.callbacks import *
from bluesky.callbacks.broker import *
from bluesky.simulators import *
from bluesky.plans import *
import numpy as np

from pyOlog.ophyd_tools import *

# Uncomment the following lines to turn on verbose messages for
# debugging.
# import logging
# ophyd.logger.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)
