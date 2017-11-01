from ophyd import (EpicsMotor, Device, Component as Cpt,
                   EpicsSignal)


class SampleStage(Device):
    rotary = Cpt(EpicsMotor, '-Ax:aY}Mtr')
    x = Cpt(EpicsMotor, '-Ax:X}Mtr')
    z = Cpt(EpicsMotor, '-Ax:Z}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')

sample_stage1 = SampleStage('XF:07BMB-ES{Stg:1', name='sample_stage1')


class HHMTrajDesc(Device):
    filename = Cpt(EpicsSignal, '-Name')
    elem = Cpt(EpicsSignal, '-Elem')
    edge = Cpt(EpicsSignal, '-Edge')


class Monochromator(Device):
    _default_configuration_attrs = ('pitch', 'roll', 'theta', 'y', 'energy')
    _default_read_attrs = ('pitch', 'roll', 'theta', 'y', 'energy')
    "Monochromator"
    bragg = Cpt(EpicsMotor, 'Mono:1-Ax:Scan}Mtr')
    energy = Cpt(EpicsMotor, 'Mono:1-Ax:E}Mtr')
    pico = Cpt(EpicsMotor, 'Mono:1-Ax:Pico}Mtr')
    diag = Cpt(EpicsMotor, 'Mono:1-Ax:Diag}Mtr')

    # The following are related to trajectory motion
    lut_number = Cpt(EpicsSignal, 'MC:03}LUT-Set')
    lut_number_rbv = Cpt(EpicsSignal, 'MC:03}LUT-Read')
    lut_start_transfer = Cpt(EpicsSignal, 'MC:03}TransferLUT')
    lut_transfering = Cpt(EpicsSignal, 'MC:03}TransferLUT-Read')
    trajectory_loading = Cpt(EpicsSignal, 'MC:03}TrajLoading')
    traj_mode = Cpt(EpicsSignal, 'MC:03}TrajFlag1-Set')
    traj_mode_rbv = Cpt(EpicsSignal, 'MC:03}TrajFlag1-Read')
    enable_ty = Cpt(EpicsSignal, 'MC:03}TrajFlag2-Set')
    enable_ty_rbv = Cpt(EpicsSignal, 'MC:03}TrajFlag2-Read')
    cycle_limit = Cpt(EpicsSignal, 'MC:03}TrajRows-Set')
    cycle_limit_rbv = Cpt(EpicsSignal, 'MC:03}TrajRows-Read')
    enable_loop = Cpt(EpicsSignal, 'MC:03}TrajLoopFlag-Set')
    enable_loop_rbv = Cpt(EpicsSignal, 'MC:03}TrajLoopFlag')

    prepare_trajectory = Cpt(EpicsSignal, 'MC:03}PrepareTraj')
    trajectory_ready = Cpt(EpicsSignal, 'MC:03}TrajInitPlc-Read')
    start_trajectory = Cpt(EpicsSignal, 'MC:03}StartTraj')
    stop_trajectory = Cpt(EpicsSignal, 'MC:03}StopTraj')
    trajectory_running = Cpt(EpicsSignal,'MC:03}TrajRunning', write_pv='MC:03}TrajRunning-Set')
    trajectory_progress = Cpt(EpicsSignal,'MC:03}TrajProgress')
    trajectory_name = Cpt(EpicsSignal, 'MC:03}TrajFilename')

    traj1 = Cpt(HHMTrajDesc, 'MC:03}Traj:1')
    traj2 = Cpt(HHMTrajDesc, 'MC:03}Traj:2')
    traj3 = Cpt(HHMTrajDesc, 'MC:03}Traj:3')
    traj4 = Cpt(HHMTrajDesc, 'MC:03}Traj:4')
    traj5 = Cpt(HHMTrajDesc, 'MC:03}Traj:5')
    traj6 = Cpt(HHMTrajDesc, 'MC:03}Traj:6')
    traj7 = Cpt(HHMTrajDesc, 'MC:03}Traj:7')
    traj8 = Cpt(HHMTrajDesc, 'MC:03}Traj:8')
    traj9 = Cpt(HHMTrajDesc, 'MC:03}Traj:9')

    angle_offset = Cpt(EpicsSignal, 'Mono:1-Ax:E}Offset', limits=True)

mono = Monochromator('XF:07BMA-OP{', name='mono')
mono.hints = {'fields': ['mono_energy', 'mono_bragg']}


class Mirror(Device):
    hor_up = Cpt(EpicsMotor, '-Ax:XU}Mtr')  # upstream
    hor_down = Cpt(EpicsMotor, '-Ax:XD}Mtr')  # downstream
    vert_up = Cpt(EpicsMotor, '-Ax:YU}Mtr')
    vert_down_in = Cpt(EpicsMotor, '-Ax:YD1}Mtr')  # downstream inboard
    vert_down_out = Cpt(EpicsMotor, '-Ax:YD2}Mtr')  # downstream outboard
    bend = Cpt(EpicsMotor, '-Ax:BD}Mtr')

cm = Mirror('XF:07BMFE-OP{Mir:Col', name='cm')
fm = Mirror('XF:07BMA-OP{Mir:FM', name='fm')


class Slits(Device):
    top = Cpt(EpicsMotor, '-Ax:T}Mtr')
    bottom = Cpt(EpicsMotor, '-Ax:B}Mtr')
    outboard = Cpt(EpicsMotor, '-Ax:O}Mtr')
    inboard = Cpt(EpicsMotor, '-Ax:I}Mtr')

foe_slits = Slits('XF:07BMA-OP{Slt:1', name='foe_slits')
jj_slits = Slits('XF:07BMB-OP{Slt:1', name='jj_slits')


ip_y_stage = EpicsMotor('XF:07BMB-OP{IBP:1-Ax:Y}Mtr', name='ip_y_stage')


class Table(Device):
    hor_up = Cpt(EpicsMotor, '-Ax:XU}Mtr')  # upstream
    hor_down = Cpt(EpicsMotor, '-Ax:XD}Mtr')  # downstream
    beam_dir = Cpt(EpicsMotor, '-Ax:Z}Mtr')
    vert_up = Cpt(EpicsMotor, '-Ax:YDU}Mtr')
    vert_down_in = Cpt(EpicsMotor, '-Ax:YDI}Mtr')  # downstream inboard
    vert_down_out = Cpt(EpicsMotor, '-Ax:YDO}Mtr')  # downstream outboard

exp_table = Table('XF:07BMB-OP{Asm:1', name='exp_table')
