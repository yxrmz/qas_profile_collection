import copy
import functools
import numpy as np
import time

import bluesky.plan_stubs as bps
import bluesky.plans as bp  # noqa
import bluesky.preprocessors as bpp

from event_model import DocumentRouter
from ophyd import Device, Component as Cpt, EpicsSignal

from bluesky.utils import ts_msg_hook
RE.msg_hook = ts_msg_hook  # noqa


class DarkSubtractionCallback(DocumentRouter):
    def __init__(self,
                 image_key='pe1_image',
                 primary_stream='primary',
                 dark_stream='dark'):
        """Initializes a dark subtraction callback.

        This will perform dark subtraction and then save to file.

        Parameters
        ----------
        image_key : str (optional)
            The detector image string
        primary_stream : str (optional)
            The primary stream name
        dark_stream : str (optional)
            The dark stream name
        """

        self.pstream = primary_stream
        self.dstream = dark_stream
        self.image_key = image_key
        self.descriptors = {}
        self._last_dark = None
        self._has_started = False

    def start(self, doc):
        if self._has_started:
            raise RuntimeError('Can handle only one run. '
                               'Two start documents found.')
        else:
            self._has_started = True
            return super().start(doc)

    def descriptor(self, doc):
        # Note: we may want to indicate background subtraction
        self.descriptors[doc['uid']] = doc
        return super().descriptor(doc)

    def event_page(self, doc):
        # Note: we may want to update the image key to indicate background
        # subtraction in the outgoing doc.
        stream_name = self.descriptors[doc['descriptor']]['name']

        if stream_name not in [self.pstream, self.dstream]:
            return doc

        if self.image_key in doc['data']:
            if stream_name == self.dstream:
                self._last_dark = doc['data'][self.image_key][-1]
                # TODO: deal with properly-paged data later
                return doc
            elif stream_name == self.pstream:
                # Actual subtraction is happening here:
                return_doc = copy.deepcopy(doc)
                dsub_images = [im - self._last_dark
                               for im in return_doc['data'][self.image_key]]

                return_doc['data'][self.image_key] = dsub_images
                return return_doc
            else:
                raise RuntimeError(f'The stream name "{stream_name}" must be '
                                   f'one of {self.pstream} or {self.dstream}')
        else:
            return doc


# From Tom on 02/21/2019:
class DarkFrameCache(Device):
    def __init__(self, *args, **kwargs):
        # self.det = det
        self.last_collected = None
        self.just_started = True
        self.update_done = False
        return super().__init__(*args, **kwargs)

    def read(self):
        return self._read

    def read_configuration(self):
        return self._read_configuration

    @property
    def configuration_attrs(self):
        return self._configuration_attrs

    @property
    def read_attrs(self):
        return self._read_attrs

    def describe(self):
        return self._describe

    def describe_configuration(self):
        return self._describe_configuration

    # def describe_configuration(self):
    #     return self.det.describe_configuration

    def collect_asset_docs(self):
        # keep track of when we get restaged to restore these
        yield from self._asset_docs_cache
        self._really_cached = self._asset_docs_cache
        self._asset_docs_cache = []

    def stage(self):
        self._asset_docs_cache = self._really_cached


def dark_plan(cam, dark_frame_cache, obsolete_secs, shutter):
    if (dark_frame_cache.just_started or  # first run after instantiation
        (dark_frame_cache.last_collected is not None and
         time.monotonic() - dark_frame_cache.last_collected > obsolete_secs)):
        tmp = yield from bps.read(shutter.status)
        init_shutter_state = tmp[shutter.status.name]['value'] if tmp is not None else None
        yield from bps.mv(shutter, 'Close')
        yield from bps.trigger(cam, group='cam')
        yield from bps.wait('cam')
        yield from bps.mv(shutter, init_shutter_state)

        teleport(cam, dark_frame_cache)
        dark_frame_cache.just_started = False
        dark_frame_cache.update_done = True
    else:
        dark_frame_cache.update_done = False


def teleport(cam, dfc):
    dfc._describe = cam.describe()
    dfc._describe_configuration = cam.describe_configuration()
    dfc._read = cam.read()
    dfc._read_configuration = cam.read_configuration()
    dfc._read_attrs = cam.read_attrs
    dfc._configuration_attrs = cam.configuration_attrs
    dfc._asset_docs_cache = list(cam.collect_asset_docs())
    dfc.last_collected = time.monotonic()


dark_frame_cache = DarkFrameCache(name='dark_frame_cache')
# Update the '_<name>' attributes which do not exist yet
teleport(pe1c, dark_frame_cache)  # noqa


def dark_frame_aware_plan(cam, dark_frame_cache, shutter=shutter_fs,
                          obsolete_secs=60, num_images=1, md=None):

    def check_and_take_darks():
        yield from dark_plan(cam, dark_frame_cache, obsolete_secs, shutter)
        if dark_frame_cache.update_done:
            yield from bpp.trigger_and_read([dark_frame_cache], name='dark')

    @bpp.stage_decorator([cam])
    @bpp.run_decorator(md=md)
    def inner_dark_frame_aware_plan():
        tmp = yield from bps.read(shutter.status)
        init_shutter_state = tmp[shutter.status.name]['value'] if tmp is not None else None
        yield from bps.mv(shutter, 'Open')

        for _ in range(num_images):
            yield from check_and_take_darks()
            yield from bpp.trigger_and_read([cam], name='primary')

        yield from bps.mv(shutter, init_shutter_state)

    return (yield from inner_dark_frame_aware_plan())


def subtract_dark(light_img, dark_img):
    res = np.asarray(light_img, dtype=int) - np.asarray(dark_img, dtype=int)
    return np.clip(res, 0, None)


def get_subtracted_image(scan_id=-1, img_field='pe1_image'):
    hdr = db[scan_id]  # noqa
    imgs_dark = np.array(list(hdr.data(img_field, stream_name='dark')))
    imgs_light = np.array(list(hdr.data(img_field, stream_name='primary')))
    dark_avg = np.mean(imgs_dark, axis=0)
    light_avg = np.mean(imgs_light, axis=0)
    sub = subtract_dark(light_avg, dark_avg)
    return sub


def plot_image(data, **kwargs):
    p = functools.partial(plt.imshow, cmap='gray', clim=(0, 500))  # noqa
    p(data, **kwargs)
<<<<<<< HEAD
    from tifffile import TiffWriter
    
    ##File saving needs to be done properly via suite-case
    with open('/nsls2/xf07bm/data/pe1_data/2019/05/16/test.tiff', 'xb') as f:
        tw = TiffWriter(f)
        tw.save(data)
=======
>>>>>>> refs/remotes/origin/master

# RE(dark_frame_aware_plan(cam, dc))
