
def fly_scan_with_apb(name: str, comment: str, n_cycles: int = 1, delay: float = 0, autofoil :bool= False, hutch_c = False, shutter=shutter_fs, **kwargs):
    '''
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times
    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata
    n_cycles : int (default = 1)
        Number of times to run the scan automatically
    delay : float (default = 0)
        Delay in seconds between scans
    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans
    '''
    print(f'Hutch C is {hutch_c}')
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []
    if autofoil:
    #if True:
        current_element = getattr(mono1, f'traj{int(mono1.lut_number_rbv.get())}').elem.get()
        try:
            yield from set_reference_foil(current_element)
        except:
            pass

    yield from bps.mv(shutter, "Open")

    if hutch_c:
        _execute_trajectory = execute_trajectory_apb_c
        flyer = flyer_apb_c
    else:
        _execute_trajectory = execute_trajectory_apb
        flyer = flyer_apb

    def plan():
        for indx in range(int(n_cycles)):
            name_n = '{} {:04d}'.format(name, indx + 1)
            yield from prep_traj_plan()
            print(f'Trajectory preparation complete at {print_now()}')
            uid = (yield from _execute_trajectory(name_n, comment=comment))
            uids.append(uid)
            print(f'Trajectory is complete {print_now()}')
            yield from bps.sleep(float(delay))
        return uids

    def final_plan():
        yield from bps.mv(flyer.motor.stop_trajectory, "1")
        det_acquiring_status = (yield from bps.rd(flyer.det.acquiring))
        if det_acquiring_status == 1:  # acquiring
            yield from bps.stop(flyer)
        __energy = mono1.energy.user_readback.get()

        print(f"After Fly scan {__energy = }")
        print_to_gui("--------------------------FLY scan finished----------------------", add_timestamp=True)

    # yield from bps.mv(shutter, "Close")


    RE.md['experiment'] = ''


    return (yield from bpp.finalize_wrapper(plan(), final_plan))


def fly_scan_with_apb_with_controlled_loop(name: str, comment: str, n_cycles: int = 1, delay: float = 0, autofoil :bool= False, hutch_c = False, shutter=shutter_fs, **kwargs):
    '''
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times
    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata
    n_cycles : int (default = 1)
        Number of times to run the scan automatically
    delay : float (default = 0)
        Delay in seconds between scans
    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans
    '''
    print(f'Hutch C is {hutch_c}')
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []
    if autofoil:
    #if True:
        current_element = getattr(mono1, f'traj{int(mono1.lut_number_rbv.get())}').elem.get()
        try:
            yield from set_reference_foil(current_element)
        except:
            pass

    yield from bps.mv(shutter, "Open")

    print('Begin Timer')
    measure_time1 = time.time()

    name_n = '{} {:04d}'.format(name, 0 + 1)
    yield from prep_traj_plan()
    print(f'Trajectory preparation complete at {print_now()}')
    if hutch_c:
        uid = (yield from execute_trajectory_apb_c(name_n, comment=comment))
    else:
        uid = (yield from execute_trajectory_apb(name_n, comment=comment))
    uids.append(uid)
    print(f'Trajectory is complete {print_now()}')
    yield from bps.sleep(float(delay))

    measure_time3 = time.time()
    measure_time2 = time.time()
    count = 1
    while count < int(n_cycles):
        if measure_time2 - measure_time1 >= 60:
            print('>>>>>>>>>>>>>>>>>>>>> 60 seconds >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            measure_time1 = measure_time2
            name_n = '{} {:04d}'.format(name, count + 1)
            yield from prep_traj_plan()
            print(f'Trajectory preparation complete at {print_now()}')
            if hutch_c:
                uid = (yield from execute_trajectory_apb_c(name_n, comment=comment))
            else:
                uid = (yield from execute_trajectory_apb(name_n, comment=comment))
            uids.append(uid)
            print(f'Trajectory is complete {print_now()}')
            yield from bps.sleep(float(delay))

            measure_time2 = time.time()
            count += 1
        else:
            if measure_time2 - measure_time3> 1:
                print(f'Time elapsed: {measure_time2 - measure_time1:.0f}s after the scan')
                measure_time3 = time.time()
            measure_time2 = time.time()

    # for indx in range(int(n_cycles)):
    #     name_n = '{} {:04d}'.format(name, indx + 1)
    #     yield from prep_traj_plan()
    #     print(f'Trajectory preparation complete at {print_now()}')
    #     if hutch_c:
    #         uid = (yield from execute_trajectory_apb_c(name_n, comment=comment))
    #     else:
    #         uid = (yield from execute_trajectory_apb(name_n, comment=comment))
    #     uids.append(uid)
    #     print(f'Trajectory is complete {print_now()}')
    #     yield from bps.sleep(float(delay))

    yield from bps.mv(shutter, "Close")


    RE.md['experiment'] = ''
    return uids


def fly_scan_with_apb_trigger(name: str, comment: str, n_cycles: int = 1, delay: float = 0, autofoil :bool= False, hutch_c = False, **kwargs):
    '''
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times
    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata
    n_cycles : int (default = 1)
        Number of times to run the scan automatically
    delay : float (default = 0)
        Delay in seconds between scans
    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans
    '''
    print(f'Hutch C is {hutch_c}')
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []
    if autofoil:
        current_element = getattr(mono1, f'traj{int(mono1.lut_number_rbv.get())}').elem.get()
        try:
            yield from set_reference_foil(current_element)
        except:
            pass

    for indx in range(int(n_cycles)):
        name_n = '{} {:04d}'.format(name, indx + 1)
        yield from prep_traj_plan()
        print(f'Trajectory preparation complete at {print_now()}')
        #yield from shutter_fs.open_plan()
        uid = (yield from execute_trajectory_apb_trigger(name_n, comment=comment))
        uids.append(uid)
        #yield from shutter_fs.close_plan()
        print(f'Trajectory is complete {print_now()}')
        yield from bps.sleep(float(delay))

    RE.md['experiment'] = ''
    return uids


def fly_scan_with_xs3(name: str, comment: str, n_cycles: int = 1, delay: float = 0,  autofoil :bool= False, hutch_c = False, **kwargs):
    '''
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times
    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata
    n_cycles : int (default = 1)
        Number of times to run the scan automatically
    delay : float (default = 0)
        Delay in seconds between scans
    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans
    '''
    print(f'Hutch C is {hutch_c}')
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []
    if autofoil:
    #if True:
        current_element = getattr(mono1, f'traj{int(mono1.lut_number_rbv.get())}').elem.get()
        try:
            yield from set_reference_foil(current_element)
        except:
            pass

    for indx in range(int(n_cycles)):
        name_n = '{} {:04d}'.format(name, indx + 1)
        yield from prep_traj_plan()
        print(f'Trajectory preparation complete at {print_now()}')
        #TODO add qas shutter
        #yield from shutter_fs.open_plan()
        uid = (yield from execute_trajectory_xs(name_n, comment=comment))
        uids.append(uid)
        #yield from shutter_fs.close_plan()
        print(f'Trajectory is complete {print_now()}')
        yield from bps.sleep(float(delay))

    RE.md['experiment'] = ''
    return uids


def fly_scan_with_pilatus(name: str, comment: str, n_cycles: int = 1, delay: float = 0, autofoil :bool= False, **kwargs):
    '''
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times
    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata
    n_cycles : int (default = 1)
        Number of times to run the scan automatically
    delay : float (default = 0)
        Delay in seconds between scans
    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans
    '''
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []
    if autofoil:
    #if True:
        current_element = getattr(mono1, f'traj{int(mono1.lut_number_rbv.get())}').elem.get()
        try:
            yield from set_reference_foil(current_element)
        except:
            pass

    for indx in range(int(n_cycles)):
        name_n = '{} {:04d}'.format(name, indx + 1)
        yield from prep_traj_plan()
        print(f'Trajectory preparation complete at {print_now()}')
        #TODO add qas shutter
        #yield from shutter_fs.open_plan()
        uid = (yield from execute_trajectory_pilatus(name_n, comment=comment))
        uids.append(uid)
        #yield from shutter_fs.close_plan()
        print(f'Trajectory is complete {print_now()}')
        yield from bps.sleep(float(delay))

    RE.md['experiment'] = ''
    return uids

def read_voltage_and_set_condition(set_voltage=2000, rise=True, channel='7'):
    read_voltage = getattr(apb, 'ch' + channel).get()
    # voltage = apb.ch7.get()
    if rise:
        if read_voltage > set_voltage:
            condition = True
        else:
            condition = False
        return condition
    else:
        if read_voltage < set_voltage:
            condition = True
        else:
            condition = False
        return condition

def fly_scan_with_hardware_trigger(name: str,
                                   comment: str,
                                   n_cycles: int = 1,
                                   delay: float = 0,
                                   set_voltage: int = 2000,
                                   channel: str = '7',
                                   rise: bool = True,
                                   autofoil: bool = False,
                                   hutch_c=False,
                                   shutter=shutter_fs,
                                   **kwargs):

    print(f'Hutch C is {hutch_c}')
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []
    if autofoil:
    #if True:
        current_element = getattr(mono1, f'traj{int(mono1.lut_number_rbv.get())}').elem.get()
        try:
            yield from set_reference_foil(current_element)
        except:
            pass

    yield from bps.mv(shutter, "Open")

    condition1 = read_voltage_and_set_condition(set_voltage=set_voltage, rise=rise, channel=channel)
    print(condition1)
    condition2 = read_voltage_and_set_condition(set_voltage=set_voltage, rise=rise, channel=channel)
    print(condition2)
    count = 0
    while count < int(n_cycles):
        if condition2 - condition1 == 1:

            name_n = '{} {:04d}'.format(name, count + 1)
            yield from prep_traj_plan()
            print(f'Trajectory preparation complete at {print_now()}')
            if hutch_c:
                uid = (yield from execute_trajectory_apb_c(name_n, comment=comment))
            else:
                uid = (yield from execute_trajectory_apb(name_n, comment=comment))
            uids.append(uid)
            print(f'Trajectory is complete {print_now()}')
            yield from bps.sleep(float(delay))
            count += 1

            condition1 = condition2
            condition2 = read_voltage_and_set_condition(set_voltage=set_voltage, rise=rise, channel=channel)
        else:
            condition1 = condition2
            condition2 = read_voltage_and_set_condition(set_voltage=set_voltage, rise=rise, channel=channel)