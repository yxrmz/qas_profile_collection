from ophyd import Component as Cpt
from ophyd import Signal

from ophyd import (SingleTrigger,
                   TIFFPlugin, ImagePlugin, DetectorBase,
                   HDF5Plugin, AreaDetector, EpicsSignal, EpicsSignalRO,
                   ROIPlugin, TransformPlugin, ProcessPlugin, PilatusDetector, 
		   PilatusDetectorCam, StatsPlugin)
from nslsii.ad33 import SingleTriggerV33, StatsPluginV33

class TIFFPluginWithFileStore(TIFFPlugin, FileStoreTIFFIterativeWrite):
    pass

class PilatusDetectorCamV33(PilatusDetectorCam):
    wait_for_plugins = Cpt(EpicsSignal, 'WaitForPlugins',
                           string=True, kind='config')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs['wait_for_plugins'] = 'Yes'

    def ensure_nonblocking(self):
        self.stage_sigs['wait_for_plugins'] = 'Yes'
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, 'ensure_nonblocking'):
                cpt.ensure_nonblocking()

class PilatusV33(SingleTriggerV33, PilatusDetector):
    cam = Cpt(PilatusDetectorCamV33, 'cam1:')
    #stats1 = Cpt(StatsPluginV33, 'Stats1:')
    #stats2 = Cpt(StatsPluginV33, 'Stats2:')
    #stats3 = Cpt(StatsPluginV33, 'Stats3:')
    #stats4 = Cpt(StatsPluginV33, 'Stats4:')
    #stats5 = Cpt(StatsPluginV33, 'Stats5:')
    #roi1 = Cpt(ROIPlugin, 'ROI1:')
    #roi2 = Cpt(ROIPlugin, 'ROI2:')
    #roi3 = Cpt(ROIPlugin, 'ROI3:')
    #roi4 = Cpt(ROIPlugin, 'ROI4:')
    #proc1 = Cpt(ProcessPlugin, 'Proc1:')

    tiff = Cpt(TIFFPluginWithFileStore,
               suffix='TIFF1:',
               write_path_template='/nsls2/data/qas-new/legacy/raw/pilatus3_data/%Y/%m/%d/',
               root='/nsls2/data/qas-new/legacy/raw')

    
    def set_exposure_time(self, exposure_time, verbosity=3):
        yield from bps.mv(self.cam.acquire_time, exposure_time, self.cam.acquire_period, exposure_time+.1)
        # self.cam.acquire_time.put(exposure_time)
        # self.cam.acquire_period.put(exposure_time+.1)
    
    def set_num_images(self, num_images):
        yield from bps.mv(self.cam.num_images, num_images)
        # self.cam.num_images = num_images

pilatus1 = PilatusV33('XF:07BM-ES{Det-Pil3}:', name='pilatus3_data')
pilatus1.tiff.read_attrs = []
pilatus1.tiff.kind = 'normal'
