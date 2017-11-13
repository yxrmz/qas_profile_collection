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


def prep_traj_plan(delay = 0.1):
    yield from bp.abs_set(hhm.prepare_trajectory, '1', wait=True)

    # Poll the trajectory ready pv
    while True:
        ret = (yield from bp.read(hhm.trajectory_ready))
        if ret is None:
            break
        is_running = ret['hhm_trajectory_ready']['value']

        if is_running:
            break
        else:
            yield from bp.sleep(.1)

    while True:
        ret = (yield from bp.read(hhm.trajectory_ready))
        if ret is None:
            break
        is_running = ret['hhm_trajectory_ready']['value']

        if is_running:
            yield from bp.sleep(.05)
        else:
            break

    yield from bp.sleep(delay)

    curr_energy = (yield from bp.read(hhm.energy))

    if curr_energy is None:
        return
        raise Exception('Could not read current energy')

    curr_energy = curr_energy['hhm_energy']['value']
    print('Curr Energy: {}'.format(curr_energy))
    if curr_energy >= 12000:
        print('>12000')
        yield from bp.mv(hhm.energy, curr_energy + 100)
        yield from bp.sleep(1)
        print('1')
        yield from bp.mv(hhm.energy, curr_energy)
