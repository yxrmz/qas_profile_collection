print(__file__)
import bluesky as bs
import bluesky.plans as bp
import bluesky.preprocessors as bpp
import bluesky.plan_stubs as bps
import time as ttime
from subprocess import call
import os
import signal


def diffraction_plan(images_per_set=1):

    '''
        This is testing a simple PerkinElmer diffraction image collection plan.
        Here we open shutter, take an image, close shutter, take a dark then stop.
    '''

    start_time = ttime.time()
        
    ## if images_per_set is not None:
       ##  yield from bps.mov(pe1c.images_per_set, images_per_set)

    ## yield from bps.stage(pe1c)

    ## yield from bps.sleep(1)

    # close fast shutter, now take a dark
    fast_shutter.close()
    yield from bps.sleep(0.5)
    ## yield from trigger_and_read(pe1c, name='dark')
    yield from bp.count([det],num=5)

    # open fast shutter
    ## yield from bps.mov(fast_shutter,1)

    fast_shutter.open()
    yield from bps.sleep(0.5)
    yield from bp.count([det],num=5)    

    # for the motors, trigger() won't be called since it doesn't exist
    ## yield from trigger_and_read(pe1c, name='primary')
        
    ## yield from bps.unstage(pe1c)

        
    ## yield from bpp.run_wrapper(imageplan(), md=dict(sample_name=sample_name))
    end_time = ttime.time()
    print(f'Duration: {end_time - start_time:.3f} sec')
