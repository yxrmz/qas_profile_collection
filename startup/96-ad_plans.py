import bluesky.plan_stubs as bps
import time as ttime


def ad_take_dark_scan(detector=pe1, exposure=1, num_dark_frames=5, shutter=shutter_ph):
    shutter_ph.close_plan()
    yield from bps.mv(detector.cam.acquire_time,exposure)
    yield from bps.mv(detector.num_dark_frames,num_dark_frames)
    yield from bps.abs_set(detector.acquire_dark_frames,1,wait=True)
    while not detector.cam.detector_state.value:
        ttime.sleep(.1)
    print(1)





