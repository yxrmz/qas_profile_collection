print(__file__)

from bluesky.plan_stubs import mv, abs_set
from nslsii.devices import TwoButtonShutter


class EPS_Shutter(Device):
    state = Cpt(EpicsSignal, 'Pos-Sts')
    cls = Cpt(EpicsSignal, 'Cmd:Cls-Cmd')
    opn = Cpt(EpicsSignal, 'Cmd:Opn-Cmd')
    error = Cpt(EpicsSignal,'Err-Sts')
    permit = Cpt(EpicsSignal, 'Permit:Enbl-Sts')
    enabled = Cpt(EpicsSignal, 'Enbl-Sts')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color = 'red'

    def open_plan(self):
        yield from mv(self.opn, 1,wait=True)

    def close_plan(self):
        yield from abs_set(self.cls, 1, wait=True)

    def open(self):
        print('Opening {}'.format(self.name))
        self.opn.put(1)

    def close(self):
        print('Closing {}'.format(self.name))
        self.cls.put(1)


class TwoButtonShutterQAS(TwoButtonShutter):
    def stop(self, success=False):
        pass


shutter_fe = TwoButtonShutterQAS('XF:07BM-PPS{Sh:FE}', name = 'FE Shutter')
shutter_fe.shutter_type = 'FE'
shutter_ph = TwoButtonShutterQAS('XF:07BMA-PPS{Sh:A}', name = 'PH Shutter')
shutter_ph.shutter_type = 'PH'


class Shutter(Device):

    def __init__(self, name):
        self.name = name
        if pb2.connected:
            self.output = pb2.do0.default_pol
            if self.output.value == 1:
                self.state = 'closed'
            elif self.output.value == 0:
                self.state = 'open'
            self.function_call = None
            self.output.subscribe(self.update_state)
        else:
            self.state = 'unknown'

    def subscribe(self, function):
        self.function_call = function

    def unsubscribe(self):
        self.function_call = None
        
    def update_state(self, pvname=None, value=None, char_value=None, **kwargs):
        if value == 1:
            self.state = 'closed'
        elif value == 0:
            self.state = 'open'
        if self.function_call is not None:
            self.function_call(pvname=pvname, value=value, char_value=char_value, **kwargs)
        
    def open(self):
        print('Opening {}'.format(self.name))
        self.output.put(0)
        self.state = 'open'
        
    def close(self):
        print('Closing {}'.format(self.name))
        self.output.put(1)
        self.state = 'closed'

    def open_plan(self):
        print('Opening {}'.format(self.name))
        yield from bps.abs_set(self.output, 0, wait=True)
        self.state = 'open'

    def close_plan(self):
        print('Closing {}'.format(self.name))
        yield from bps.abs_set(self.output, 1, wait=True)
        self.state = 'closed'

fast_shutter = Shutter(name = 'Fast Shutter')
fast_shutter.shutter_type = 'Fast'

'''
Here is the amplifier definitionir_

'''


class ICAmplifier(Device):

    gain = Cpt(EpicsSignal,'gain')
    risetime = Cpt(EpicsSignal,'risetime')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def get_gain(self):
        return self.gain.get()+3

    def set_gain(self, gain):
        self.gain.set(gain-3)



i0_amp = ICAmplifier('XF:07BM:K428:A:',name='i0_amp')
 
it_amp = ICAmplifier('XF:07BM:K428:B:',name='it_amp')

ir_amp = ICAmplifier('XF:07BM:K428:C:',name='ir_amp')

iff_amp = ICAmplifier('XF:07BM:K428:D:',name='iff_amp')

'''
ir_amp = ICAmplifier('XF:08IDB-CT{', gain_0='ES-DO}2_10_0', gain_1='ES-DO}2_10_1',
                     gain_2='ES-DO}2_10_2', hspeed_bit='ES-DO}2_10_3', bw_10mhz_bit='ES-DO}2_10_4', bw_1mhz_bit='ES-DO}2_10_5',
                     lnoise='Amp-LN}Ir', hspeed='Amp-HS}Ir', bwidth='Amp-BW}Ir', name='ir_amp')

iff_amp = ICAmplifier('XF:08IDB-CT{', gain_0='ES-DO}2_11_0', gain_1='ES-DO}2_11_1',
                     gain_2='ES-DO}2_11_2', hspeed_bit='ES-DO}2_11_3', bw_10mhz_bit='ES-DO}2_11_4', bw_1mhz_bit='ES-DO}2_11_5',
lnoise='Amp-LN}If', hspeed='Amp-HS}If', bwidth='Amp-BW}If', name='iff_amp')
self.gain_1 = EpicsSignal(self.prefix + gain_1, name=self.name + '_gain_1')
        self.gain_2 = EpicsSignal(self.prefix + gain_2, name=self.name + '_gain_2')
        self.hspeed_bit = EpicsSignal(self.prefix + hspeed_bit, name=self.name + '_hspeed_bit')
        self.bw_10mhz_bit = EpicsSignal(self.prefix + bw_10mhz_bit, name=self.name + '_bw_10mhz_bit')
        self.bw_1mhz_bit = EpicsSignal(self.prefix + bw_1mhz_bit, name=self.name + '_bw_1mhz_bit')
        self.low_noise_gain = EpicsSignal(self.prefix + lnoise, name=self.name + '_lnoise')
        self.high_speed_gain = EpicsSignal(self.prefix + hspeed, name=self.name + '_hspeed')
        self.band_width = EpicsSignal(self.prefix + bwidth, name=self.name + '_bwidth')
        self.par = par
       


    def set_gain(self, value: int, high_speed: bool):

        val = int(value) - 2
        if not ((high_speed and (1 <= val < 7)) or (not high_speed and (0 <= val < 6))):
            print('{} invalid value. Ignored...'.format(self.name))
            return 'Aborted'

        if high_speed:
            val -= 1
            self.low_noise_gain.put(0)
            self.high_speed_gain.put(val + 1)
            self.hspeed_bit.put(1)
        else:
            self.low_noise_gain.put(val + 1)
            self.high_speed_gain.put(0)
            self.hspeed_bit.put(0)

        self.gain_0.put((val >> 0) & 1)
        self.gain_1.put((val >> 1) & 1)
        self.gain_2.put((val >> 2) & 1)

    def set_gain_plan(self, value: int, high_speed: bool):

        val = int(value) - 2
        if not ((high_speed and (1 <= val < 7)) or (not high_speed and (0 <= val < 6))):
            print('{} invalid value. Ignored...'.format(self.name))
            return 'Aborted'

        if high_speed:
            val -= 1
            yield from bp.abs_set(self.low_noise_gain, 0)
            yield from bp.abs_set(self.high_speed_gain, val + 1)
            yield from bp.abs_set(self.hspeed_bit, 1)
        else:
            yield from bp.abs_set(self.low_noise_gain, val + 1)
            yield from bp.abs_set(self.high_speed_gain, 0)
            yield from bp.abs_set(self.hspeed_bit, 0)

        yield from bp.abs_set(self.gain_0, (val >> 0) & 1)
        yield from bp.abs_set(self.gain_1, (val >> 1) & 1)
        yield from bp.abs_set(self.gain_2, (val >> 2) & 1)

    def get_gain(self):
        if self.low_noise_gain.value == 0:
            return [self.high_speed_gain.enum_strs[self.high_speed_gain.value], 1]
        elif self.high_speed_gain.value == 0:
            return [self.low_noise_gain.enum_strs[self.low_noise_gain.value], 0]
        else:
            return ['0', 0]


'''
