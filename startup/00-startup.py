print(__file__)
import nslsii

beamline_id = 'qas'

nslsii.configure_base(get_ipython().user_ns, beamline_id, bec=False)


# At the end of every run, verify that files were saved and
# print a confirmation message.
from bluesky.callbacks.broker import verify_files_saved
# RE.subscribe(post_run(verify_files_saved), 'stop')

# Optional: set any metadata that rarely changes.

# these should *always* be QAS
RE.md['group'] = beamline_id
RE.md['beamline_id'] = beamline_id.upper()
# isstools reads these

# check these keys exist, if not set to default
keys = ["PI", "PROPOSAL", "SAF", "year", "cycle", "proposal_id"]
defaults = ["No PI", None, None, 2018, 1, None]
for key, default in zip(keys, defaults):
    if key not in RE.md:
        print("Warning {} not in RE.md.".format(key))
        print("Set to default : {}".format(default))
        RE.md[key] = default

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

# Enabling (2018C3) logging of the message hook into a log file.
import os
import sys
import datetime
import functools

# TODO: to be removed and imported from bluesky once
# https://github.com/NSLS-II/bluesky/pull/1117 is reviewed, merged, released,
# and pushed to the beamline.
def ts_msg_hook(msg, file=sys.stdout):
    t = '{:%H:%M:%S.%f}'.format(datetime.datetime.now())
    msg_fmt = '{: <17s} -> {!s: <15s} args: {}, kwargs: {}'.format(
        msg.command,
        msg.obj.name if hasattr(msg.obj, 'name') else msg.obj,
        msg.args,
        msg.kwargs)
    print('{} {}'.format(t, msg_fmt), file=file)

# The logs will be saved to the profile dir.
profile_startup_dir = get_ipython().profile_dir.startup_dir
# The name of the log file consists of the beamline id and the timestamp at the
# startup of bsui, so we don't have collisions of the names.
log_filename = f'{beamline_id}-bsui-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.log'
log_filename = os.path.join(profile_startup_dir, log_filename)

print(f'\n!!! The logs will be written to {log_filename} !!!\n')
file = open(log_filename, 'a')

func = functools.partial(ts_msg_hook, file=file)
RE.msg_hook = func
