import uuid
from collections import namedtuple
import os
import time as ttime
from ophyd import (ProsilicaDetector, SingleTrigger, Component as Cpt, Device,
                   EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin, ROIPlugin,
                   DeviceStatus)
from ophyd import DeviceStatus, set_and_wait
from bluesky.examples import NullStatus

from databroker.assets.handlers_base import HandlerBase


class BPM(ProsilicaDetector, SingleTrigger):
    image = Cpt(ImagePlugin, 'image1:')
    stats1 = Cpt(StatsPlugin, 'Stats1:')
    stats2 = Cpt(StatsPlugin, 'Stats2:')
    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    counts = Cpt(EpicsSignal, 'Pos:Counts')
    # Dan Allan guessed about the nature of these signals. Fix them if you need them.
    ins = Cpt(EpicsSignal, 'Cmd:In-Cmd')
    ret = Cpt(EpicsSignal, 'Cmd:Out-Cmd')
    switch_insert = Cpt(EpicsSignalRO, 'Sw:InLim-Sts')
    switch_retract = Cpt(EpicsSignalRO, 'Sw:OutLim-Sts')
    polarity = 'pos'

    def insert(self):
        self.ins.put(1)

    def retract(self):
        self.ret.put(1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.clear()  # default stage sigs do not apply

class CAMERA(ProsilicaDetector, SingleTrigger):
    image = Cpt(ImagePlugin, 'image1:')
    stats1 = Cpt(StatsPlugin, 'Stats1:')
    stats2 = Cpt(StatsPlugin, 'Stats2:')
    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    polarity = 'pos'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.clear()  # default stage sigs do not apply


colmirror_diag = CAMERA('XF:07BM-BI{Mir:Col}', name='colmirror_diag')
screen_diag = CAMERA('XF:07BM-BI{FS:1}', name='screen_diag') # HOW TO CALL CAMERA UNDER FT DIAGNOSTICS > Diagnostic Screen
mono_diag = CAMERA('XF:07BM-BI{Mono:1}', name='mono_diag')
dcr_diag = CAMERA('XF:07BM-BI{Diag:1}', name='dcr_diag')

for camera in [colmirror_diag, screen_diag, mono_diag, dcr_diag]:
    camera.read_attrs = ['stats1', 'stats2']
    camera.image.read_attrs = ['array_data']
    camera.stats1.read_attrs = ['total', 'centroid']
    camera.stats2.read_attrs = ['total', 'centroid']


class Encoder(Device):
    """This class defines components but does not implement actual reading.
    See EncoderFS and EncoderParser"""
    pos_I = Cpt(EpicsSignal, '}Cnt:Pos-I')
    sec_array = Cpt(EpicsSignal, '}T:sec_Bin_')
    nsec_array = Cpt(EpicsSignal, '}T:nsec_Bin_')
    pos_array = Cpt(EpicsSignal, '}Cnt:Pos_Bin_')
    index_array = Cpt(EpicsSignal, '}Cnt:Index_Bin_')
    data_array = Cpt(EpicsSignal, '}Data_Bin_')
    # The '$' in the PV allows us to write 40 chars instead of 20.
    filepath = Cpt(EpicsSignal, '}ID:File.VAL$', string=True)
    dev_name = Cpt(EpicsSignal, '}DevName')

    filter_dy = Cpt(EpicsSignal, '}Fltr:dY-SP')
    filter_dt = Cpt(EpicsSignal, '}Fltr:dT-SP')
    reset_counts = Cpt(EpicsSignal, '}Rst-Cmd')

    ignore_rb = Cpt(EpicsSignal, '}Ignore-RB')
    ignore_sel = Cpt(EpicsSignal, '}Ignore-Sel')

    resolution = 1;

    def __init__(self, *args, reg, **kwargs):
        super().__init__(*args, **kwargs)
        self._ready_to_collect = False
        self._reg = reg
        if self.connected:
            self.ignore_sel.put(1)
            # self.filter_dt.put(10000)


class EncoderFS(Encoder):
    "Encoder Device, when read, returns references to data in filestore."
    chunk_size = 1024

    def stage(self):
        "Set the filename and record it in a 'resource' document in the filestore database."

        if(self.connected):
            print(self.name, 'stage')
            DIRECTORY = '/epics/'
            rpath = 'pb_data'
            filename = 'en_' + str(uuid.uuid4())[:6]
            full_path = os.path.join(rpath, filename)
            self._full_path = os.path.join(DIRECTORY, full_path)  # stash for future reference
            if len(self._full_path) > 40:
                raise RuntimeError("Stupidly, EPICS limits the file path to 80 characters. "
                               "Choose a different DIRECTORY with a shorter path. (I know....)")
            self._full_path = os.path.join(DIRECTORY, full_path)  # stash for future reference
            self.filepath.put(self._full_path)
            self.resource_uid = self._reg.register_resource(
                'PIZZABOX_ENC_FILE_TXT',
                DIRECTORY, full_path,
                {'chunk_size': self.chunk_size})

            super().stage()

    def unstage(self):
        if(self.connected):
            set_and_wait(self.ignore_sel, 1)
            return super().unstage()

    def kickoff(self):
        print('kickoff', self.name)
        self._ready_to_collect = True
        "Start writing data into the file."

        set_and_wait(self.ignore_sel, 0)

        # Return a 'status object' that immediately reports we are 'done' ---
        # ready to collect at any time.
        return NullStatus()

    def complete(self):
        print('complete', self.name, '| filepath', self._full_path)
        if not self._ready_to_collect:
            raise RuntimeError("must called kickoff() method before calling complete()")
        # Stop adding new data to the file.
        set_and_wait(self.ignore_sel, 1)
        #while not os.path.isfile(self._full_path):
        #    ttime.sleep(.1)
        return NullStatus()

    def collect(self):
        """
        Record a 'datum' document in the filestore database for each encoder.
        Return a dictionary with references to these documents.
        """
        print('collect', self.name)
        self._ready_to_collect = False

        # Create an Event document and a datum record in filestore for each line
        # in the text file.
        now = ttime.time()
        ttime.sleep(1)  # wait for file to be written by pizza box
        if os.path.isfile(self._full_path):
            with open(self._full_path, 'r') as f:
                linecount = len(list(f))
            chunk_count = linecount // self.chunk_size + int(linecount % self.chunk_size != 0)
            for chunk_num in range(chunk_count):
                datum_uid = self._reg.register_datum(
                    self.resource_uid, {'chunk_num': chunk_num})
                data = {self.name: datum_uid}
                yield {'data': data,
                       'timestamps': {key: now for key in data}, 'time': now}
        else:
            print('collect {}: File was not created'.format(self.name))

    def describe_collect(self):
        # TODO Return correct shape (array dims)
        now = ttime.time()
        return {self.name: {self.name:
                     {'filename': self._full_path,
                      'devname': self.dev_name.value,
                      'source': 'pizzabox-enc-file',
                      'external': 'FILESTORE:',
                      'shape': [1024, 5],
                      'dtype': 'array'}}}


class DigitalOutput(Device):
    """ DigitalOutput """
    enable = Cpt(EpicsSignal, '}Ena-Cmd')
    period_sp = Cpt(EpicsSignal, '}Period-SP')
    unit_sel = Cpt(EpicsSignal, '}Unit-Sel')
    dutycycle_sp = Cpt(EpicsSignal, '}DutyCycle-SP')
    default_pol = Cpt(EpicsSignal, '}Dflt-Sel')

    def __init__(self, *args, reg, **kwargs):
        self._reg = reg
        super().__init__(*args, **kwargs)
        self._ready_to_collect = False
        if self.connected:
            self.enable.put(0)


class DigitalInput(Device):
    """This class defines components but does not implement actual reading.
    See DigitalInputFS """
    data_I = Cpt(EpicsSignal, '}Raw:Data-I_')
    sec_array = Cpt(EpicsSignal, '}T:sec_Bin_')
    nsec_array = Cpt(EpicsSignal, '}T:nsec_Bin_')
    index_array = Cpt(EpicsSignal, '}Cnt:Index_Bin_')
    data_array = Cpt(EpicsSignal, '}Data_Bin_')
    # The '$' in the PV allows us to write 40 chars instead of 20.
    filepath = Cpt(EpicsSignal, '}ID:File.VAL$', string=True)
    dev_name = Cpt(EpicsSignal, '}DevName')

    ignore_rb = Cpt(EpicsSignal, '}Ignore-RB')
    ignore_sel = Cpt(EpicsSignal, '}Ignore-Sel')

    def __init__(self, *args, reg, **kwargs):
        self._reg = reg
        super().__init__(*args, **kwargs)
        self._ready_to_collect = False
        if self.connected:
            self.ignore_sel.put(1)


class DIFS(DigitalInput):
    "Encoder Device, when read, returns references to data in filestore."
    chunk_size = 1024

    def stage(self):
        "Set the filename and record it in a 'resource' document in the filestore database."


        print(self.name, 'stage')
        DIRECTORY = '/GPFS/xf08id/'
        rpath = 'pizza_box_data'
        filename = 'di_' + str(uuid.uuid4())[:6]
        full_path = os.path.join(rpath, filename)
        self._full_path = os.path.join(DIRECTORY, full_path)  # stash for future reference
        if len(self._full_path) > 40:
            raise RuntimeError("Stupidly, EPICS limits the file path to 80 characters. "
                           "Choose a different DIRECTORY with a shorter path. (I know....)")
        self._full_path = os.path.join(DIRECTORY, full_path)  # stash for future reference
        self.filepath.put(self._full_path)
        self.resource_uid = self._reg.register_resource(
            'PIZZABOX_DI_FILE_TXT',
            DIRECTORY, full_path,
            {'chunk_size': self.chunk_size})

        super().stage()

    def unstage(self):
        set_and_wait(self.ignore_sel, 1)
        return super().unstage()

    def kickoff(self):
        print('kickoff', self.name)
        self._ready_to_collect = True
        "Start writing data into the file."

        set_and_wait(self.ignore_sel, 0)

        # Return a 'status object' that immediately reports we are 'done' ---
        # ready to collect at any time.
        return NullStatus()

    def complete(self):
        print('complete', self.name, '| filepath', self._full_path)
        if not self._ready_to_collect:
            raise RuntimeError("must called kickoff() method before calling complete()")
        # Stop adding new data to the file.
        set_and_wait(self.ignore_sel, 1)
        #while not os.path.isfile(self._full_path):
        #    ttime.sleep(.1)
        return NullStatus()

    def collect(self):
        """
        Record a 'datum' document in the filestore database for each encoder.
        Return a dictionary with references to these documents.
        """
        print('collect', self.name)
        self._ready_to_collect = False

        # Create an Event document and a datum record in filestore for each line
        # in the text file.
        now = ttime.time()
        ttime.sleep(1)  # wait for file to be written by pizza box
        if os.path.isfile(self._full_path):
            with open(self._full_path, 'r') as f:
                linecount = len(list(f))
            chunk_count = linecount // self.chunk_size + int(linecount % self.chunk_size != 0)
            for chunk_num in range(chunk_count):
                datum_uid = self._reg.register_datum(self.resource_uid,
                                                     {'chunk_num': chunk_num})
                data = {self.name: datum_uid}

                yield {'data': data,
                       'timestamps': {key: now for key in data}, 'time': now}
        else:
            print('collect {}: File was not created'.format(self.name))

    def describe_collect(self):
        # TODO Return correct shape (array dims)
        now = ttime.time()
        return {self.name: {self.name:
                     {'filename': self._full_path,
                      'devname': self.dev_name.value,
                      'source': 'pizzabox-di-file',
                      'external': 'FILESTORE:',
                      'shape': [1024, 5],
                      'dtype': 'array'}}}

class PizzaBoxFS(Device):
    ts_sec = Cpt(EpicsSignal, '}T:sec-I')
    #internal_ts_sel = Cpt(EpicsSignal, '}T:Internal-Sel')

    enc1 = Cpt(EncoderFS, ':1', reg=db.reg)
    enc2 = Cpt(EncoderFS, ':2', reg=db.reg)
    enc3 = Cpt(EncoderFS, ':3', reg=db.reg)
    enc4 = Cpt(EncoderFS, ':4', reg=db.reg)
    di = Cpt(DIFS, ':DI', reg=db.reg)
    do0 = Cpt(DigitalOutput, '-DO:0', reg=db.reg)
    do1 = Cpt(DigitalOutput, '-DO:1', reg=db.reg)
    do2 = Cpt(DigitalOutput, '-DO:2', reg=db.reg)
    do3 = Cpt(DigitalOutput, '-DO:3', reg=db.reg)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # must use internal timestamps or no bytes are written

    def kickoff(self):
        "Call encoder.kickoff() for every encoder."
        for attr_name in ['enc1', 'enc2', 'enc3', 'enc4']:
            status = getattr(self, attr_name).kickoff()
            print("Eli's test", self.attr_name)
        # it's fine to just return one of the status objects
        return status

    def collect(self):
        "Call encoder.collect() for every encoder."
        # Stop writing data to the file in all encoders.
        for attr_name in ['enc1', 'enc2', 'enc3', 'enc4']:
            set_and_wait(getattr(self, attr_name).ignore_sel, 1)
        # Now collect the data accumulated by all encoders.
        for attr_name in ['enc1', 'enc2', 'enc3', 'enc4']:
            yield from getattr(self, attr_name).collect()


pb1 = PizzaBoxFS('XF:07BM-CT{Enc01', name = 'pb1')
pb1.enc1.pulses_per_deg = 9400000/360
