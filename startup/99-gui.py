print(__file__)
print("Loading isstools, preparing GUI...")
from PyQt5.QtWidgets import QApplication
import functools
import isstools.xlive
import collections
import atexit

import PyQt5

from bluesky.examples import motor
motor.move = motor.set


detector_dictionary = {#colmirror_diag.name: {'obj': colmirror_diag, 'elements': [colmirror_diag.stats1.total.name, colmirror_diag.stats2.total.name]},
                    #screen_diag.name: {'obj': screen_diag, 'elements': [screen_diag.stats1.total.name, screen_diag.stats2.total.name]},
                    #mono_diag.name: {'obj': mono_diag, 'elements': [mono_diag.stats1.total.name, mono_diag.stats2.total.name]},
                    #dcr_diag.name: {'obj': dcr_diag, 'elements': [dcr_diag.stats1.total.name, dcr_diag.stats2.total.name]},
                    #pba1.adc1.name: {'obj': pba1.adc1, 'elements': ['pba1_adc1_volt']},
                    #pba1.adc3.name: {'obj': pba1.adc3, 'elements': ['pba1_adc3_volt']},
                    #pba1.adc4.name: {'obj': pba1.adc4, 'elements': ['pba1_adc4_volt']},
                    #pba1.adc5.name: {'obj': pba1.adc5, 'elements': ['pba1_adc5_volt']},
                    #pba1.adc6.name: {'obj': pba1.adc6, 'elements': ['pba1_adc6_volt']},
                    #pba1.adc7.name: {'obj': pba1.adc7, 'elements': ['pba1_adc7_volt']},
                    #pba1.adc8.name: {'obj': pba1.adc8, 'elements': ['pba1_adc8_volt']},
                    #pb1.enc1.name: {'obj': pb1.enc1, 'channels': ['pb1_enc1_pos_I']},
                    'I0': {'device': apb_ave, 'channels': ['apb_ave_ch1_mean']},
                    'It': {'device': apb_ave, 'channels': ['apb_ave_ch2_mean']},
                    'Ir': {'device': apb_ave, 'channels': ['apb_ave_ch3_mean']},
                    'If': {'device': apb_ave, 'channels': ['apb_ave_ch4_mean']},
}



motors_dictionary = {jj_slits_hutchB.xctr.name: {'name': jj_slits_hutchB.xctr.name, 'description':jj_slits_hutchB.xctr.name, 'object': jj_slits_hutchB.xctr},
                     jj_slits_hutchC.xctr.name: {'name': jj_slits_hutchC.xctr.name, 'description':jj_slits_hutchC.xctr.name, 'object': jj_slits_hutchC.xctr},
                     drifts.drifts_rot.name: {'name': drifts.drifts_rot.name, 'description':drifts.drifts_rot.name, 'object': drifts.drifts_rot},
                     drifts.drifts_x.name: {'name': drifts.drifts_x.name, 'description':drifts.drifts_x.name, 'object': drifts.drifts_x},
                     beamstop.horizontal.name: {'name': beamstop.horizontal.name, 'description': 'Beamstop Horizontal', 'object':beamstop.horizontal},
                     beamstop.vertical.name: {'name': beamstop.vertical.name, 'description': beamstop.vertical.name, 'object': beamstop.vertical},
                     ibp_hutchB.name: {'name': ibp_hutchB.name, 'description': ibp_hutchB.name, 'object': ibp_hutchB},
                     ibp_hutchC.name: {'name': ibp_hutchC.name, 'description': ibp_hutchC.name, 'object': ibp_hutchC},
                     sample_stage1.rotary.name: {'name': sample_stage1.rotary.name, 'description':sample_stage1.rotary.name, 'object':sample_stage1.rotary},
                     sample_stage1.x.name: {'name': sample_stage1.x.name, 'description':sample_stage1.x.name, 'object':sample_stage1.x},
                     sample_stage1.y.name: {'name': sample_stage1.y.name, 'description':sample_stage1.y.name, 'object':sample_stage1.y},
                     sample_stage1.z.name: {'name': sample_stage1.z.name, 'description':sample_stage1.z.name, 'object':sample_stage1.z},
                     sample_stage1.theta.name: {'name': sample_stage1.theta.name, 'description':sample_stage1.theta.name, 'object':sample_stage1.theta},
                     sample_stage1.chi.name: {'name': sample_stage1.chi.name, 'description':sample_stage1.chi.name, 'object':sample_stage1.chi},
                    }

shutters_dictionary = {
                       shutter_fe.name: shutter_fe,
                       shutter_ph.name: shutter_ph,
                       shutter_fs.name: shutter_fs,
                       }

service_plan_funcs = {
    'get_offsets': get_offsets,
    'xs_count': xs_count,
    }

sample_stages = [{'x': sample_stage1.x.name, 'y': sample_stage1.y.name}]

aux_plan_funcs = {
    'Set Reference Foil': set_reference_foil,
    'Get Reference Foil': get_reference_foil,
    'General Scan': general_scan,
}

plan_funcs = {
    'Fly scan': fly_scan_with_apb,
    'Fly scan w/SDD': fly_scan_with_xs3,
}

app = QApplication(sys.argv)

newApp = PyQt5.QtWidgets.QApplication(sys.argv)

xlive_gui = isstools.xlive.XliveGui(plan_funcs=plan_funcs,
                                    diff_plans=[count_qas, dark_frame_preprocessor],
                                    aux_plan_funcs =aux_plan_funcs,
                                    service_plan_funcs=service_plan_funcs,
                                    prep_traj_plan= prep_traj_plan,
                                    RE=RE,
                                    db=db,
                                    apb = apb,
                                    accelerator=nsls_ii,
                                    mono=mono1,
                                    sdd = xs,
                                    shutters_dict=shutters_dictionary,
                                    det_dict=detector_dictionary,
                                    motors_dict=motors_dictionary,
                                    general_scan_func=general_scan,
                                    sample_stage = sample_stage1,
                                    window_title="XLive@QAS/7-BM NSLS-II",
                                   )

sys.stdout = xlive_gui.emitstream_out

def xlive():
    xlive_gui.show()



xlive()
