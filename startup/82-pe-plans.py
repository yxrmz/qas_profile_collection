import time
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp



def pe_acquisition_plan(dets, fs, sample_name='', images_per_set=None):
    '''
        This is testing a simple acquisition plan.
        Here we open shutter, take an image, close shutter, take a dark then
            stop.
        dets : dets to read from
        fs : the fast shutter
        sample_name : the sample name
    '''
    start_time = time.time()

    def _pe_acquisition_plan():
        for det in dets:
            if images_per_set is not None:
                yield from bps.mov(det.images_per_set, images_per_set)

        for det in dets:
            yield from bps.stage(det)

        yield from bps.sleep(1)

        # close fast shutter, now take a dark
        # yield from bps.mov(fs, 0)
        yield from bpp.trigger_and_read(dets, name='dark')

        # open fast shutter
        # yield from bps.mov(fs, 1)
        yield from bpp.trigger_and_read(dets, name='primary')

        for det in dets:
            yield from bps.unstage(det)

    yield from bpp.run_wrapper(_pe_acquisition_plan(), md=dict(sample_name=sample_name))
    end_time = time.time()
    print(f'Duration: {end_time - start_time:.3f} sec')
