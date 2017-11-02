import bluesky as bs
import bluesky.plans as bp
import time as ttime
from subprocess import call
import os
import signal


def general_scan_plan(detectors, motor, rel_start, rel_stop, num):
    
    plan = bp.relative_scan(detectors, motor, rel_start, rel_stop, num)
    
    if hasattr(detectors[0], 'kickoff'):
        plan = bp.fly_during_wrapper(plan, detectors)

    yield from plan
