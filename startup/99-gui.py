print(__file__)
print("Loading isstools, preparing GUI...")

import functools
import isstools.xlive
import collections
import atexit
from bluesky.examples import motor
motor.move = motor.set

# TODO : replace with message broker
# Needs the lightflow environment
from lightflow.config import Config
from lightflow.workflows import start_workflow



detector_dictionary = {colmirror_diag.name: {'obj': colmirror_diag, 'elements': [colmirror_diag.stats1.total.name, colmirror_diag.stats2.total.name]},
                       screen_diag.name: {'obj': screen_diag, 'elements': [screen_diag.stats1.total.name, screen_diag.stats2.total.name]},
                       mono_diag.name: {'obj': mono_diag, 'elements': [mono_diag.stats1.total.name, mono_diag.stats2.total.name]},
                       dcr_diag.name: {'obj': dcr_diag, 'elements': [dcr_diag.stats1.total.name, dcr_diag.stats2.total.name]},
                       #pba1.adc1.name: {'obj': pba1.adc1, 'elements': ['pba1_adc1_volt']},
                       pba1.adc3.name: {'obj': pba1.adc3, 'elements': ['pba1_adc3_volt']},
                       pba1.adc4.name: {'obj': pba1.adc4, 'elements': ['pba1_adc4_volt']},
                       pba1.adc5.name: {'obj': pba1.adc5, 'elements': ['pba1_adc5_volt']},
                       pba1.adc6.name: {'obj': pba1.adc6, 'elements': ['pba1_adc6_volt']},
                       pba1.adc7.name: {'obj': pba1.adc7, 'elements': ['pba1_adc7_volt']},
                       pba1.adc8.name: {'obj': pba1.adc8, 'elements': ['pba1_adc8_volt']},
                       pb1.enc1.name: {'obj': pb1.enc1, 'elements': ['pb1_enc1_pos_I']},
                      }

motors_dictionary = {jj_slits.top.name: {'name': jj_slits.top.name, 'description':jj_slits.top.name, 'object': jj_slits.top},
                     jj_slits.bottom.name: {'name': jj_slits.bottom.name, 'description':jj_slits.bottom.name, 'object': jj_slits.bottom},
                     jj_slits.outboard.name: {'name': jj_slits.outboard.name, 'description':jj_slits.outboard.name, 'object': jj_slits.outboard},
                     jj_slits.inboard.name: {'name': jj_slits.inboard.name, 'description':jj_slits.inboard.name, 'object': jj_slits.inboard},
                     sample_stage1.x.name: {'name': sample_stage1.x.name, 'description':sample_stage1.x.name, 'object':sample_stage1.x},
                     sample_stage1.y.name: {'name': sample_stage1.y.name, 'description':sample_stage1.y.name, 'object':sample_stage1.y},
                     sample_stage1.z.name: {'name': sample_stage1.z.name, 'description':sample_stage1.z.name, 'object':sample_stage1.z},
                     sample_stage1.rotary.name: {'name': sample_stage1.rotary.name, 'description':sample_stage1.rotary.name, 'object':sample_stage1.rotary},
                     fm.bend.name: {'name': fm.bend.name, 'description': fm.bend.name, 'object':fm.bend},
                     ip_y_stage.name: {'name': ip_y_stage.name, 'description': ip_y_stage.name, 'object':ip_y_stage},
                    }

shutters_dictionary = collections.OrderedDict([(shutter_fe.name, shutter_fe),
                                         (shutter_ph.name, shutter_ph),])
                                         #(shutter.name, shutter)])

sample_stages = [{'x': sample_stage1.x.name, 'y': sample_stage1.y.name}]

print(mono1)
xlive_gui = isstools.xlive.XliveGui(plan_funcs=[tscan, get_offsets], 
                                 prep_traj_plan=prep_traj_plan, 
                                 RE=RE,
                                 db=db, 
                                 accelerator=nsls_ii,
                                 hhm=mono1,#None,
                                 shutters_dict=shutters_dictionary,
                                 det_dict=detector_dictionary,
                                 motors_dict=motors_dictionary,
                                 general_scan_func=general_scan,
                                 sample_stages = sample_stages,
                                 job_submitter=submit_lightflow_job,
                                 bootstrap_servers=['cmb01:9092', 'cmb02:9092'],
                                 kafka_topic="qas-processing", 
                                 window_title="XLive @QAS/11-BMNSLS-II",
                                 )

sys.stdout = xlive_gui.emitstream_out

def xlive():
    xlive_gui.show()

#from isstools.xview import XviewGui
#xview_gui = XviewGui(PB_PULSES_PER_DEGREE)


xlive()
