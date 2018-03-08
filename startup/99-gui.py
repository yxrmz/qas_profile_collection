import isstools.gui
import collections
import atexit
from bluesky.examples import motor
motor.move = motor.set


detector_dictionary = {colmirror_diag.name: {'obj': colmirror_diag, 'elements': [colmirror_diag.stats1.total.name, colmirror_diag.stats2.total.name]},
                       screen_diag.name: {'obj': screen_diag, 'elements': [screen_diag.stats1.total.name, screen_diag.stats2.total.name]},
                       mono_diag.name: {'obj': mono_diag, 'elements': [mono_diag.stats1.total.name, mono_diag.stats2.total.name]},
                       dcr_diag.name: {'obj': dcr_diag, 'elements': [dcr_diag.stats1.total.name, dcr_diag.stats2.total.name]},
                       #pba1.adc1.name: {'obj': pba1.adc1, 'elements': ['pba1_adc1_volt']},
                       pba1.adc6.name: {'obj': pba1.adc6, 'elements': ['pba1_adc6_volt']},
                       pba1.adc7.name: {'obj': pba1.adc7, 'elements': ['pba1_adc7_volt']},
                       pb1.enc1.name: {'obj': pb1.enc1, 'elements': ['pb1_enc1_pos_I']},
                      }

motors_dictionary = {foe_slits.top.name: {'name': foe_slits.top.name, 'description':foe_slits.top.name, 'object': foe_slits.top},
                     foe_slits.bottom.name: {'name': foe_slits.bottom.name, 'description':foe_slits.bottom.name, 'object': foe_slits.bottom},
                     foe_slits.outboard.name: {'name': foe_slits.outboard.name, 'description':foe_slits.outboard.name, 'object': foe_slits.outboard},
                     foe_slits.inboard.name: {'name': foe_slits.inboard.name, 'description':foe_slits.inboard.name, 'object': foe_slits.inboard},
                     foe_slits.bottom.name: {'name': foe_slits.bottom.name, 'description':foe_slits.bottom.name, 'object': foe_slits.bottom},
                     jj_slits.top.name: {'name': jj_slits.top.name, 'description':jj_slits.top.name, 'object': jj_slits.top},
                     jj_slits.bottom.name: {'name': jj_slits.bottom.name, 'description':jj_slits.bottom.name, 'object': jj_slits.bottom},
                     jj_slits.outboard.name: {'name': jj_slits.outboard.name, 'description':jj_slits.outboard.name, 'object': jj_slits.outboard},
                     jj_slits.inboard.name: {'name': jj_slits.inboard.name, 'description':jj_slits.inboard.name, 'object': jj_slits.inboard},
                     fe_slits.top.name: {'name': fe_slits.top.name, 'description':fe_slits.top.name, 'object': fe_slits.top},
                     fe_slits.bottom.name: {'name': fe_slits.bottom.name, 'description':fe_slits.bottom.name, 'object': fe_slits.bottom},
                     fe_slits.outboard.name: {'name': fe_slits.outboard.name, 'description':fe_slits.outboard.name, 'object': fe_slits.outboard},
                     fe_slits.inboard.name: {'name': fe_slits.inboard.name, 'description':fe_slits.inboard.name, 'object': fe_slits.inboard},
                     mono1.bragg.name: {'name': mono1.bragg.name, 'description': mono1.bragg.name, 'object':mono1.bragg},
                     mono1.energy.name: {'name': mono1.energy.name, 'description': mono1.energy.name, 'object':mono1.energy},
                     mono1.pico.name: {'name': mono1.pico.name, 'description': mono1.pico.name, 'object':mono1.pico},
                     sample_stage1.x.name: {'name': sample_stage1.x.name, 'description':sample_stage1.x.name, 'object':sample_stage1.x},
                     sample_stage1.y.name: {'name': sample_stage1.y.name, 'description':sample_stage1.y.name, 'object':sample_stage1.y},
                     sample_stage1.z.name: {'name': sample_stage1.z.name, 'description':sample_stage1.z.name, 'object':sample_stage1.z},
                     sample_stage1.rotary.name: {'name': sample_stage1.rotary.name, 'description':sample_stage1.rotary.name, 'object':sample_stage1.rotary},
                     cm.hor_up.name: {'name': cm.hor_up.name, 'description': cm.hor_up.name, 'object':cm.hor_up},
                     cm.hor_down.name: {'name': cm.hor_down.name, 'description': cm.hor_down.name, 'object':cm.hor_down},
                     cm.vert_up.name: {'name': cm.vert_up.name, 'description': cm.vert_up.name, 'object':cm.vert_up},
                     cm.vert_down_in.name: {'name': cm.vert_down_in.name, 'description': cm.vert_down_in.name, 'object':cm.vert_down_in},
                     cm.vert_down_out.name: {'name': cm.vert_down_out.name, 'description': cm.vert_down_out.name, 'object':cm.vert_down_out},
                     cm.bend.name: {'name': cm.bend.name, 'description': cm.bend.name, 'object':cm.bend},
                     fm.hor_up.name: {'name': fm.hor_up.name, 'description': fm.hor_up.name, 'object':fm.hor_up},
                     fm.hor_down.name: {'name': fm.hor_down.name, 'description': fm.hor_down.name, 'object':fm.hor_down},
                     fm.vert_up.name: {'name': fm.vert_up.name, 'description': fm.vert_up.name, 'object':fm.vert_up},
                     fm.vert_down_in.name: {'name': fm.vert_down_in.name, 'description': fm.vert_down_in.name, 'object':fm.vert_down_in},
                     fm.vert_down_out.name: {'name': fm.vert_down_out.name, 'description': fm.vert_down_out.name, 'object':fm.vert_down_out},
                     fm.bend.name: {'name': fm.bend.name, 'description': fm.bend.name, 'object':fm.bend},
                     ip_y_stage.name: {'name': ip_y_stage.name, 'description': ip_y_stage.name, 'object':ip_y_stage},
                     exp_table.hor_up.name: {'name': exp_table.hor_up.name, 'description': exp_table.hor_up.name, 'object':exp_table.hor_up},
                     exp_table.hor_down.name: {'name': exp_table.hor_down.name, 'description': exp_table.hor_down.name, 'object':exp_table.hor_down},
                     exp_table.beam_dir.name: {'name': exp_table.beam_dir.name, 'description': exp_table.beam_dir.name, 'object':exp_table.beam_dir},
                     exp_table.vert_up.name: {'name': exp_table.vert_up.name, 'description': exp_table.vert_up.name, 'object':exp_table.vert_up},
                     exp_table.vert_down_in.name: {'name': exp_table.vert_down_in.name, 'description': exp_table.vert_down_in.name, 'object':exp_table.vert_down_in},
                     exp_table.vert_down_out.name: {'name': exp_table.vert_down_out.name, 'description': exp_table.vert_down_out.name, 'object':exp_table.vert_down_out}
                    }

shutters_dictionary = collections.OrderedDict([(shutter_fe.name, shutter_fe),
                                         (shutter_ph.name, shutter_ph),])
                                         #(shutter.name, shutter)])

sample_stages = [{'x': sample_stage1.x.name, 'y': sample_stage1.y.name}]

print(mono1)
xlive_gui = isstools.gui.ScanGui(plan_funcs=[tscan, get_offsets], 
                                 prep_traj_plan=prep_traj_plan, 
                                 RE=RE,
                                 db=db, 
                                 accelerator=nsls_ii,
                                 hhm=mono1,#None,
                                 shutters_dict=shutters_dictionary,
                                 det_dict=detector_dictionary,
                                 motors_dict=motors_dictionary,
                                 general_scan_func=general_scan,
                                 sample_stages = sample_stages)

def xlive():
    xlive_gui.show()

xlive()
