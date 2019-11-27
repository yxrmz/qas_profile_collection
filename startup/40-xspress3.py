from ophyd.areadetector import (AreaDetector, PixiradDetectorCam, ImagePlugin,
                                TIFFPlugin, StatsPlugin, HDF5Plugin,
                                ProcessPlugin, ROIPlugin, TransformPlugin,
                                OverlayPlugin)
from ophyd.areadetector.plugins import PluginBase
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.device import BlueskyInterface
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.areadetector.filestore_mixins import (FileStoreIterativeWrite,
                                                 FileStoreHDF5IterativeWrite,
                                                 FileStoreTIFFSquashing,
                                                 FileStoreTIFF)
from ophyd import Signal
from ophyd.status import SubscriptionStatus
from ophyd.sim import NullStatus  # TODO: remove after complete/collect are defined
from ophyd import Component as Cpt

from hxntools.handlers import register
register(db)

from pathlib import PurePath
from hxntools.detectors.xspress3 import (XspressTrigger, Xspress3Detector,
                                         Xspress3Channel, Xspress3FileStore, logger)
from databroker.assets.handlers import Xspress3HDF5Handler, HandlerBase
from isstools.trajectory.trajectory import trajectory_manager

import bluesky.plans as bp
import bluesky.plan_stubs as bps


class QasXspress3Detector(XspressTrigger, Xspress3Detector):
    roi_data = Cpt(PluginBase, 'ROIDATA:')
    channel1 = Cpt(Xspress3Channel, 'C1_', channel_num=1, read_attrs=['rois'])
    channel2 = Cpt(Xspress3Channel, 'C2_', channel_num=2, read_attrs=['rois'])
    channel3 = Cpt(Xspress3Channel, 'C3_', channel_num=3, read_attrs=['rois'])
    channel4 = Cpt(Xspress3Channel, 'C4_', channel_num=4, read_attrs=['rois'])
    # create_dir = Cpt(EpicsSignal, 'HDF5:FileCreateDir')

    hdf5 = Cpt(Xspress3FileStore, 'HDF5:',
               read_path_template='/nsls2/xf07bm/data/x3m/%Y/%m/%d/',
               root='/nsls2/xf07bm/data/',
               write_path_template='/nsls2/xf07bm/data/x3m/%Y/%m/%d/',
               )

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        if configuration_attrs is None:
            configuration_attrs = ['external_trig', 'total_points',
                                   'spectra_per_point', 'settings',
                                   'rewindable']
        if read_attrs is None:
            read_attrs = ['channel1', 'channel2', 'channel3', 'channel4', 'hdf5']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)
        # self.create_dir.put(-3)

    def stop(self):
        ret = super().stop()
        self.hdf5.stop()
        return ret

    def stage(self):
        if self.spectra_per_point.get() != 1:
            raise NotImplementedError(
                "multi spectra per point not supported yet")
        ret = super().stage()
        return ret

    def unstage(self):
        self.settings.trigger_mode.put(0)  # 'Software'
        super().unstage()

    # Currently only using three channels. Uncomment these to enable more
    # channels:
    # channel5 = C(Xspress3Channel, 'C5_', channel_num=5)
    # channel6 = C(Xspress3Channel, 'C6_', channel_num=6)
    # channel7 = C(Xspress3Channel, 'C7_', channel_num=7)
    # channel8 = C(Xspress3Channel, 'C8_', channel_num=8)


xs = QasXspress3Detector('XF:07BMB-ES{Xsp:1}:', name='xs')
for n in [1, 2, 3, 4]:
    getattr(xs, f'channel{n}').rois.read_attrs = ['roi{:02}'.format(j) for j in [1, 2, 3, 4]]
xs.hdf5.num_extra_dims.put(0)
xs.channel2.vis_enabled.put(1)
xs.channel3.vis_enabled.put(1)
xs.settings.num_channels.put(4)


class XSFlyer:
    def __init__(self, *, pb, di, pb_triggers, xs_dets, an_dets, motor):
        """
        The flyer based on a single encoder pizza-box and multiple xspress3 devices running a mono.

        Parameters
        ----------
        pb : an encoder pizza-box orchestrating the experiment
        di : a digital input to timestamp trigger pulses
        pb_triggers : list
            a list of names of the trigger signals (e.g., 'do1') from the pizza-box digital outputs.
            It's possible to configure up to 4 triggers per pizza-box, triggering a corresponding xspress3 detector each.
        xs_dets : list
            a list of ophyd devices for the xspress3 detectors (up to 4 xspress3 detectors per 1 pizza-box)
        an_dets : list
            a list of analog detectors to be triggered
        motor : a monochromator motor
        """
        self.name = f'{pb.name}-{"-".join([xs_det.name for xs_det in xs_dets])}-{"-".join([an_det.name for an_det in an_dets])}-{motor.name}-{self.__class__.__name__}'
        self.pb = pb
        self.di = di
        self.pb_triggers = pb_triggers
        self.xs_dets = xs_dets
        self.an_dets = an_dets
        self.motor = motor

        # self.parent = None
        self.num_points = {}
        self._motor_status = None

    def __repr__(self):
        return f"""\
    Flyer '{self.name}' with the following config:

        - encoder pizza-box  : {self.pb.name}
        - pizza-box triggers : {', '.join([x for x in self.pb_triggers])}
        - xspress3 detectors : {', '.join([x.name for x in self.xs_dets])}
        - analog detectors   : {', '.join([x.name for x in self.an_dets])}
        - motor              : {self.motor.name}
"""

    def kickoff(self, *args, **kwargs):
        # Set all required signals in xspress3
        self._calc_num_points()
        for xs_det in self.xs_dets:
            xs_det.stage()
            xs_det.settings.num_images.put(self.num_points[xs_det.name])

        # self.det.external_trig.put(True)  # This is questionable, if we need it or not.
        # Next line should take care of everything.
        # xspress3 CSS:
        for xs_det in self.xs_dets:
            xs_det.settings.trigger_mode.put(3)  # "Acquisition Controls and Status" (top left pane) -->
                                                 # "Trigger" selection button 'TTL Veto Only'
            xs_det.hdf5.capture.put(1)           # "File Saving" (left bottom pane) --> "Start File Saving" button
            xs_det.settings.acquire.put(1)       # "Acquisition Controls and Status" (top left pane) --> "Start" button

        # analog pizza-boxes:
        for an_det in self.an_dets:
            an_det.stage()
            an_det.kickoff()

        # Parameters of the encoder pizza-boxes:
        # (J8B channel for pb2)
        self.pb.stage()
        self.di.stage()
        for pb_trigger in self.pb_triggers:
            getattr(self.pb.parent, pb_trigger).enable.put(1)

        self._motor_status = self.motor.set('start')

        return NullStatus()

    def complete(self):
        def callback_motor():
            # Parameters of the encoder pizza-boxes:
            # (J8B channel for pb2)
            for pb_trigger in self.pb_triggers:
                getattr(self.pb.parent, pb_trigger).enable.put(0)

            for xs_det in self.xs_dets:
                xs_det.settings.trigger_mode.put(1)  # "Acquisition Controls and Status" (top left pane) -->
                                                     # "Trigger" selection button 'Internal'
                xs_det.hdf5.capture.put(0)           # "File Saving" (left bottom pane) --> "Stop File Saving" button
                xs_det.settings.acquire.put(0)       # "Acquisition Controls and Status" (top left pane) --> "Stop" button

            for an_det in self.an_dets:
                an_det.complete()

        self._motor_status.add_callback(callback_motor)

        return self._motor_status

    def describe_collect(self):
        """
        In [3]: hdr.stream_names
        Out[3]:
        ['pba1_adc5',
         'pba1_adc8',
         'pba1_adc7',
         'pba1_adc4',
         'xs',
         'pb2_enc1',
         'pba1_adc3',
         'pba1_adc6']

        In [4]: hdr.table(stream_name='pba1_adc5')
        Out[4]:
                                         time                             pba1_adc5
        seq_num
        1       2019-11-27 15:08:43.058514118  b0d95db8-f2c4-49ab-a918-014e02775b3a

        In [5]: hdr.table(stream_name='pba1_adc5', fill=True)
        Out[5]:
                                         time                                          pba1_adc5
        seq_num
        1       2019-11-27 15:08:43.058514118            timestamp       adc
        0      1.574885e...

        In [6]: hdr.table(stream_name='pb1_enc1', fill=True)
        Out[6]:
        Empty DataFrame
        Columns: []
        Index: []

        In [7]: hdr.table(stream_name='pb2_enc1', fill=True)
        Out[7]:
        Empty DataFrame
        Columns: []
        Index: []

        In [8]: hdr.table(stream_name='xs', fill=True)
        Out[8]:
        Empty DataFrame
        Columns: []
        Index: []
        """
        return_dict = {}

        # xspress3 detectors:
        for xs_det in self.xs_dets:
            return_dict[xs_det.name] = {f'{xs_det.name}': {'source': 'xspress3',
                                                           'dtype': 'array',
                                                           'shape': [-1, -1],
                                                           'external': 'FILESTORE:'}}
        # analog pizza-boxes:
        for an_det in self.an_dets:
            return_dict[an_det.name] = an_det.describe_collect()[an_det.name]

        # encoder pizza-box:
        return_dict[self.pb.name] = self.pb.describe_collect()[self.pb.name]
        # TODO: add di
        return return_dict

    def collect_asset_docs(self):
        for xs_det in self.xs_dets:
            yield from xs_det.collect_asset_docs()
        # for an_det in self.an_dets:
        #     yield from an_det.collect_asset_docs()
        # yield from self.pb.collect_asset_docs()

    def collect(self):
        for xs_det in self.xs_dets:
            xs_det.unstage()
        for an_det in self.an_dets:
            an_det.unstage()
        self.pb.unstage()
        self.di.unstage()

        def collect_all():
            # for xs_det in self.xs_dets:
            #     yield from xs_det.collect()
            for an_det in self.an_dets:
                yield from an_det.collect()
            yield from self.pb.collect()

        return collect_all()

    def _calc_num_points(self):
        """
        Calculate a number of points for the xspress3 detectors.

        "Acquisition Controls and Status" (top left pane) --> "Number Of Frames" field
        """
        tr = trajectory_manager(self.motor)
        info = tr.read_info(silent=True)
        lut = str(int(self.motor.lut_number_rbv.get()))
        traj_duration = int(info[lut]['size']) / 16_000
        for pb_trigger, xs_det in zip(self.pb_triggers, self.xs_dets):
            if getattr(self.pb.parent, pb_trigger).unit_sel.get() == 0:
                 multip = 1e-6  # micro-seconds
            else:
                 multip = 1e-3  # mili-seconds
            acq_num_points = traj_duration / (getattr(self.pb.parent, pb_trigger).period_sp.get() * multip) * 1.3
            self.num_points[xs_det.name] = int(round(acq_num_points, ndigits=0))


xsflyer_pb2 = XSFlyer(pb=pb2.enc1,
                      di=pb2.di,
                      pb_triggers=['do1'],
                      xs_dets=[xs],
                      an_dets=[pba1.adc3, pba1.adc4, pba1.adc5, pba1.adc6, pba1.adc7, pba1.adc8],
                      motor=mono1)


# This is necessary for when the ioc restarts
# we have to trigger one image for the hdf5 plugin to work correclty
# else, we get file writing errors
# xs.hdf5.warmup()

# Hints:
for n in [1, 2]:
    getattr(xs, f'channel{n}').rois.roi01.value.kind = 'hinted'

# import skbeam.core.constants.xrf as xrfC
#
# interestinglist = ['Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U']
#
# elements = dict()
# element_edges = ['ka1','ka2','kb1','la1','la2','lb1','lb2','lg1','ma1']
# element_transitions = ['k', 'l1', 'l2', 'l3', 'm1', 'm2', 'm3', 'm4', 'm5']
# for i in interestinglist:
#     elements[i] = xrfC.XrfElement(i)
#
# def setroi(roinum, element, edge):
#     '''
#     Set energy ROIs for Vortex SDD.  Selects elemental edge given current energy if not provided.
#     roinum      [1,2,3]     ROI number
#     element     <symbol>    element symbol for target energy
#     edge                    optional:  ['ka1','ka2','kb1','la1','la2','lb1','lb2','lg1','ma1']
#     '''
#
#     cur_element = xrfC.XrfElement(element)
#
#     e_ch = int(cur_element.emission_line[edge] * 1000)
#
#     for (n, d) in xs.channels.items():
#         d.set_roi(roinum, e_ch-200, e_ch+200, name=element + '_' + edge)
#         getattr(d.rois, f'roi{roinum:02d}').kind = 'normal'
#     print("ROI{} set for {}-{} edge.".format(roinum, element, edge))
#
#
# def clearroi(roinum=None):
#     if roinum is None:
#         roinum = [1, 2, 3]
#     try:
#         roinum = list(roinum)
#     except TypeError:
#         roinum = [roinum]
#
#     # xs.channel1.rois.roi01.clear
#     for (n, d) in xs.channels.items():
#         for roi in roinum:
#              cpt = getattr(d.rois, f'roi{roi:02d}')
#              cpt.clear()
#              cpt.kind = 'omitted'
#
xs.settings.configuration_attrs = ['acquire_period',
			           'acquire_time',
			           'gain',
			           'image_mode',
			           'manufacturer',
			           'model',
			           'num_exposures',
			           'num_images',
			           'temperature',
			           'temperature_actual',
			           'trigger_mode',
			           'config_path',
			           'config_save_path',
			           'invert_f0',
			           'invert_veto',
			           'xsp_name',
			           'num_channels',
			           'num_frames_config',
			           'run_flags',
                                   'trigger_signal']

for n, d in xs.channels.items():
    roi_names = ['roi{:02}'.format(j) for j in [1, 2, 3, 4]]
    d.rois.read_attrs = roi_names
    d.rois.configuration_attrs = roi_names
    for roi_n in roi_names:
        getattr(d.rois, roi_n).value_sum.kind = 'omitted'


def xs_plan():
    yield from bps.mv(xsflyer_pb2.motor, 'prepare')
    yield from bp.fly([xsflyer_pb2])
