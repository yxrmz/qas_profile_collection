import sys
from xas.file_io import validate_file_exists
import time as ttime
from datetime import datetime
from ophyd.status import SubscriptionStatus
from termcolor import colored


class GPFSNotConnectedError(Exception):
    ...


class FlyerAPB:
    def __init__(self, det, pbs, motor):
        self.name = f'{det.name}-{"-".join([pb.name for pb in pbs])}-flyer'
        self.parent = None
        self.det = det
        self.pbs = pbs  # a list of passed pizza-boxes
        self.motor = motor
        self._motor_status = None
        self._mount_exists = False

    def kickoff(self, *args, **kwargs):
        # set_and_wait(self.det.trig_source, 1)
        # TODO: handle it on the plan level
        # set_and_wait(self.motor, 'prepare')

        # Check that the filesystem is mounted at
        # "/nsls2/data/qas-new/legacy/raw/apb" on "xf07bmb-anpb1":
        if not self._mount_exists:
            msg = "\n\n    /nsls2/data/qas-new/legacy/raw/apb is {}mounted correctly @ xf07bmb-anpb1{}\n"
            status = self.det.check_apb_gpfs_status()  # returns True for mounted, and False for not-mounted
            if not status:
                self._mount_exists = False
                error_msg = colored(msg.format("NOT ", ".\n    Contact Beamline staff for instructions."), "red")
                print(error_msg, file=sys.stdout, flush=True)
                raise GPFSNotConnectedError(error_msg)
            else:
                self._mount_exists = True
                print(colored(msg.format("", ""), "green"), file=sys.stdout, flush=True)

        def callback(value, old_value, **kwargs):

            if int(round(old_value)) == 0 and int(round(value)) == 1:
                # Now start mono move
                self._motor_status = self.motor.set('start')
                return True
            else:
                return False

        print(f'     !!!!! {datetime.now()} Flyer kickoff is complete at')

        streaming_st = SubscriptionStatus(self.det.streaming, callback)

        # Staging analog detector:
        self.det.stage()

        # Staging all encoder detectors:
        for pb in self.pbs:
            pb.stage()
            pb.kickoff()

        # Start apb after encoder pizza-boxes, which will trigger the motor.
        self.det.stream.set(1)

        return streaming_st

    def complete(self):

        def callback_det(value, old_value, **kwargs):
            if int(round(old_value)) == 1 and int(round(value)) == 0:
                # print(f'     !!!!! {datetime.now()} callback_det')
                return True
            else:
                return False
        streaming_st = SubscriptionStatus(self.det.streaming, callback_det)

        def callback_motor(status):
            # print(f'     !!!!! {datetime.now()} callback_motor')

            # print('      I am sleeping for 10 seconds')
            # ttime.sleep(10.0)
            # print('      Done sleeping for 10 seconds')

            # TODO: see if this 'set' is still needed (also called in self.det.unstage()).
            # Change it to 'put' to have a blocking call.
            # self.det.stream.set(0)

            self.det.stream.put(0)
            self.det.complete()

            for pb in self.pbs:
                pb.complete()

        self._motor_status.add_callback(callback_motor)
        return streaming_st & self._motor_status

    def describe_collect(self):
        return_dict = self.det.describe_collect()
        # Also do it for all pizza-boxes
        for pb in self.pbs:
            return_dict[pb.name] = pb.describe_collect()[pb.name]

        return return_dict

    def collect_asset_docs(self):
        yield from self.det.collect_asset_docs()
        for pb in self.pbs:
            yield from pb.collect_asset_docs()

    def collect(self):
        self.det.unstage()
        for pb in self.pbs:
            pb.unstage()

        def collect_all():
            for pb in self.pbs:
                yield from pb.collect()
            yield from self.det.collect()
        # print(f'collect is being returned ({ttime.ctime(ttime.time())})')
        return collect_all()

flyer_apb = FlyerAPB(det=apb_stream, pbs=[pb1.enc1], motor=mono1)


def get_traj_duration():
    tr = trajectory_manager(mono1)
    info = tr.read_info(silent=True)
    lut = str(int(mono1.lut_number_rbv.get()))
    return int(info[lut]['size']) / 16000


def get_md_for_scan(name, mono_scan_type, plan_name, experiment, **metadata):
        interp_fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.raw"
        interp_fn = validate_file_exists(interp_fn)
        #print(f'Storing data at {interp_fn}')
        curr_traj = getattr(mono1, 'traj{:.0f}'.format(mono1.lut_number_rbv.get()))

        i0_gainB  = i0_amp.get_gain()
        it_gainB  = it_amp.get_gain()
        ir_gainB  = ir_amp.get_gain()
        iff_gainB = iff_amp.get_gain()

        # Terrible hack again following Eli's foot steps
        foil_elem = get_reference_foil()
        i0_gainB = i0_amp.get_gain()
        it_gainB = it_amp.get_gain()
        ir_gainB = ir_amp.get_gain()
        iff_gainB = iff_amp.get_gain()

        mfc1B_he = mfc1_he.flow_rb.get()
        mfc2B_n2 = mfc2_n2.flow_rb.get()
        mfc3B_ar = mfc3_ar.flow_rb.get()
        mfc4B_n2 = mfc4_n2.flow_rb.get()
        mfc5B_ar = mfc5_ar.flow_rb.get()

        incident_beampathB_y = ibp_hutchB.user_readback.get()

        incident_slitsB_top = jj_slits_hutchB.top.user_readback.get()
        incident_slitsB_bottom = jj_slits_hutchB.bottom.user_readback.get()
        incident_slitsB_inboard = jj_slits_hutchB.inboard.user_readback.get()
        incident_slitsB_outboard = jj_slits_hutchB.outboard.user_readback.get()

        sample_stageB_rot = sample_stage1.rotary.user_readback.get()
        sample_stageB_x = sample_stage1.x.user_readback.get()
        sample_stageB_y = sample_stage1.y.user_readback.get()
        sample_stageB_z = sample_stage1.z.user_readback.get()

        pe_y = pe_pos.vertical.user_readback.get()

        cm_xu = cm.hor_up.user_readback.get()
        cm_xd = cm.hor_down.user_readback.get()
        # End of terrible hack


        try:
            full_element_name = getattr(elements, curr_traj.elem.get()).name.capitalize()
        except:
            full_element_name = curr_traj.elem.get()
        md = {'plan_args': {},
              'plan_name': plan_name,
              'experiment': experiment,
              'name': name,
              'foil_element': [foil_elem],
              'interp_filename': interp_fn,
              'angle_offset': str(mono1.angle_offset.get()),
              'trajectory_name': mono1.trajectory_name.get(),
              'element': curr_traj.elem.get(),
              'element_full': full_element_name,
              'edge': curr_traj.edge.get(),
              'e0': curr_traj.e0.get(),
              'pulses_per_degree': mono1.pulses_per_deg,
              'keithley_gainsB': [i0_gainB, it_gainB, ir_gainB, iff_gainB],
              'ionchamber_ratesB': [mfc1B_he, mfc2B_n2, mfc3B_ar, mfc4B_n2, mfc5B_ar],
              'incident_beampathB': [incident_beampathB_y],
              'incident_slits': [incident_slitsB_top, incident_slitsB_bottom, incident_slitsB_inboard,
                                 incident_slitsB_outboard],
              'sample_stageB': [sample_stageB_rot, sample_stageB_x, sample_stageB_y, sample_stageB_z],
              'pe_vertical': [pe_y],
              'cm_horizontal': [cm_xu, cm_xd]
              }
        for indx in range(8):
            md[f'ch{indx+1}_offset'] = getattr(apb, f'ch{indx+1}_offset').get()
            # amp = getattr(apb, f'amp_ch{indx+1}')


            # if amp:
            #     md[f'ch{indx+1}_amp_gain']= amp.get_gain()[0]
            # else:
            #     md[f'ch{indx+1}_amp_gain']=0
        #print(f'METADATA \n {md} \n')
        md.update(**metadata)
        return md



def execute_trajectory_apb(name, **metadata):
    md = get_md_for_scan(name,
                         'fly_scan',
                         'execute_trajectory_apb',
                         'fly_energy_scan_apb',
                         **metadata)
    yield from bp.fly([flyer_apb], md=md)
