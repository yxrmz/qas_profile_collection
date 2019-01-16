import time as ttime
import os
from copy import deepcopy
import ophyd
from ophyd.areadetector import (PerkinElmerDetector, ImagePlugin,
                                TIFFPlugin, StatsPlugin, HDF5Plugin,
                                ProcessPlugin, ROIPlugin, TransformPlugin)
from ophyd.device import BlueskyInterface
from ophyd.areadetector.trigger_mixins import SingleTrigger, MultiTrigger
from ophyd.areadetector.filestore_mixins import (FileStoreIterativeWrite,
                                                 FileStoreHDF5IterativeWrite,
                                                 FileStoreTIFFSquashing,
                                                 FileStoreTIFF)
from ophyd import Signal, EpicsSignal, EpicsSignalRO # Tim test
from ophyd import Component as C
from ophyd import StatusBase
from ophyd.status import DeviceStatus

# monkey patch for trailing slash problem
def _ensure_trailing_slash(path):
    """
    'a/b/c' -> 'a/b/c/'

    EPICS adds the trailing slash itself if we do not, so in order for the
    setpoint filepath to match the readback filepath, we need to add the
    trailing slash ourselves.
    """
    newpath = os.path.join(path, '')
    if newpath[0] != '/' and newpath[-1] == '/':
        # make it a windows slash
        newpath = newpath[:-1]
    return newpath

ophyd.areadetector.filestore_mixins._ensure_trailing_slash = _ensure_trailing_slash


# from shutter import sh1


class XPDTIFFPlugin(TIFFPlugin, FileStoreTIFFSquashing,
                    FileStoreIterativeWrite):
    pass

class XPDPerkinElmer(PerkinElmerDetector):
    image = C(ImagePlugin, 'image1:')
    _default_configuration_attrs = (
        PerkinElmerDetector._default_configuration_attrs +
        ('images_per_set', 'number_of_sets', 'pixel_size'))
    tiff = C(XPDTIFFPlugin, 'TIFF1:',
             write_path_template='/a/b/c/',
             read_path_template='/a/b/c',
             cam_name='cam',  # used to configure "tiff squashing"
             proc_name='proc',  # ditto
             read_attrs=[],
             root='/nsls2/xf07bm/')

    # hdf5 = C(XPDHDF5Plugin, 'HDF1:',
    #          write_path_template='G:/pe1_data/%Y/%m/%d/',
    #          read_path_template='/direct/XF28ID2/pe1_data/%Y/%m/%d/',
    #          root='/direct/XF28ID2/')

    proc = C(ProcessPlugin, 'Proc1:')

    # These attributes together replace `num_images`. They control
    # summing images before they are stored by the detector (a.k.a. "tiff
    # squashing").
    images_per_set = C(Signal, value=1, add_prefix=())
    number_of_sets = C(Signal, value=1, add_prefix=())

    pixel_size = C(Signal, value=.0002, kind='config')
    stats1 = C(StatsPluginV33, 'Stats1:')
    stats2 = C(StatsPluginV33, 'Stats2:')
    stats3 = C(StatsPluginV33, 'Stats3:')
    stats4 = C(StatsPluginV33, 'Stats4:')
    stats5 = C(StatsPluginV33, 'Stats5:')

    trans1 = C(TransformPlugin, 'Trans1:')

    roi1 = C(ROIPlugin, 'ROI1:')
    roi2 = C(ROIPlugin, 'ROI2:')
    roi3 = C(ROIPlugin, 'ROI3:')
    roi4 = C(ROIPlugin, 'ROI4:')

    # dark_image = C(SavedImageSignal, None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([(self.cam.trigger_mode, 'Internal')])


class ContinuousAcquisitionTrigger(BlueskyInterface):
    """
    This trigger mixin class records images when it is triggered.

    It expects the detector to *already* be acquiring, continously.
    """
    def __init__(self, *args, plugin_name=None, image_name=None, **kwargs):
        if plugin_name is None:
            raise ValueError("plugin name is a required keyword argument")
        super().__init__(*args, **kwargs)
        self._plugin = getattr(self, plugin_name)
        if image_name is None:
            image_name = '_'.join([self.name, 'image'])
        self._plugin.stage_sigs[self._plugin.auto_save] = 'No'
        self.cam.stage_sigs[self.cam.image_mode] = 'Continuous'
        self._plugin.stage_sigs[self._plugin.file_write_mode] = 'Capture'
        self._image_name = image_name
        self._status = None
        self._num_captured_signal = self._plugin.num_captured
        self._num_captured_signal.subscribe(self._num_captured_changed)
        self._save_started = False

    def stage(self):
        if self.cam.acquire.get() != 1:
            raise RuntimeError("The ContinuousAcuqisitionTrigger expects "
                               "the detector to already be acquiring.")
        return super().stage()
        # put logic to look up proper dark frame
        # die if none is found

    def trigger(self):
        "Trigger one acquisition."
        if not self._staged:
            raise RuntimeError("This detector is not ready to trigger."
                               "Call the stage() method before triggering.")
        self._save_started = False
        self._status = DeviceStatus(self)
        self._desired_number_of_sets = self.number_of_sets.get()
        self._plugin.num_capture.put(self._desired_number_of_sets)
        self.dispatch(self._image_name, ttime.time())
        # reset the proc buffer, this needs to be generalized
        self.proc.reset_filter.put(1)
        self._plugin.capture.put(1)  # Now the TIFF plugin is capturing.
        return self._status

    def _num_captured_changed(self, value=None, old_value=None, **kwargs):
        "This is called when the 'acquire' signal changes."
        if self._status is None:
            return
        if value == self._desired_number_of_sets:
            # This is run on a thread, so exceptions might pass silently.
            # Print and reraise so they are at least noticed.
            try:
                self.tiff.write_file.put(1)
            except Exception as e:
                print(e)
                raise
            self._save_started = True
        if value == 0 and self._save_started:
            self._status._finished()
            self._status = None
            self._save_started = False

class PerkinElmerContinuous(ContinuousAcquisitionTrigger, XPDPerkinElmer):
    pass

# PE1c detector configurations:
pe1_pv_prefix = 'XF:07BM-ES{Det:PE1}'
pe1c = PerkinElmerContinuous(pe1_pv_prefix, name='pe1',
                             read_attrs=['tiff', 'stats1.total'],
                             plugin_name='tiff')


# Update read/write paths for all the detectors in once:
for det in [pe1c]:

    # det.tiff.read_path_template = f'/nsls2/xf07bm/data/{det.name}_data/%Y/%m/%d/'
    det.tiff.read_path_template = f'C:/Users/xf07bm/DiffractionData/PE1_DATA/%Y/%m/%d/\\' # for WINDOWS local directory 
    # det.tiff.write_path_template = f'G:\\{det.name}_data\\%Y\\%m\\%d\\'
    # det.tiff.write_path_template = f'Z:\\data\\{det.name}_data\\%Y\\%m\\%d\\'
    det.tiff.write_path_template = f'C:/Users/xf07bm/DiffractionData/PE1_DATA/%Y/%m/%d/\\'  # for WINDOWS local directory

    det.cam.bin_x.kind = 'config'
    det.cam.bin_y.kind = 'config'
    
# some defaults, as an example of how to use this
# pe1.configure(dict(images_per_set=6, number_of_sets=10))
