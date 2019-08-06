import uuid

def pe_count(filename='', exposure = 1, num_images:int = 1, num_dark_images:int = 1):

    year     = RE.md['year']
    cycle    = RE.md['cycle']
    proposal = RE.md['PROPOSAL']
   
    print(proposal)

    #write_path_template = 'Z:\\data\\pe1_data\\%Y\\%m\\%d\\'
    write_path_template = f'Z:\\users\\{year}\\{cycle}\\{proposal}XRD\\'
    file_path = datetime.now().strftime(write_path_template)
    filename = filename + str(uuid.uuid4())[:6]


    if num_dark_images > 0:
        yield from bps.mv(pe1.num_dark_images ,num_dark_images )
        yield from bps.mv(shutter_fs, 'Close')
        yield from bps.mv(pe1c, 'acquire_dark')

    yield from bps.mv(pe1.tiff.file_name,filename)
    yield from bps.mv(pe1.cam.image_mode, 'Multiple')
    yield from bps.mv(pe1.cam.acquire_time, exposure)
    yield from bps.mv(pe1.cam.num_images,num_images)
    
    #file_number = int(pe1.tiff.file_number.get())
    #if file_number = 1: 
    yield from bps.mv(pe1.tiff.file_number,1)

    yield from bps.mv(pe1.tiff.file_path, file_path)
    yield from bps.mv(shutter_fs, 'Open')
    yield from bps.sleep(0.5)
    yield from bps.mv(pe1.tiff.file_write_mode, 'Stream')
    yield from bps.mv(pe1.tiff.capture, 1)
    yield from bps.mv(pe1c, 'acquire_light')
    yield from bps.mv(pe1.tiff.capture, 0)


    #     def prep_traj_plan(delay=0.1):
    #         yield from bps.mv(pec1, 'dacquire')
    #         yield from bps.sleep(delay)
    #
    #     #yield from  bps.mv(pe1.num_dark_images,num_dark_images)
    #
    # pe1.tiff_file_name.put(os.path.join(DIRECTORY,filename))



    yield from bps.mv(pe1.cam.acquire_time,exposure)

    # # def stage(self):
    # #     "Set the filename and record it in a 'resource' document in the filestore database."
    #
    #
    #     print(self.name, 'stage')
    #     DIRECTORY = datetime.now().strftime(self.write_path_template)
    #     #DIRECTORY = "/nsls2/xf07bm/data/pb_data"
    #
    #     filename = 'di_' + str(uuid.uuid4())[:6]
    #     self._full_path = os.path.join(DIRECTORY, filename)  # stash for future reference
    #
    #     self.filepath.put(self._full_path)
    #     self.resource_uid = self._reg.register_resource(
    #         'PIZZABOX_DI_FILE_TXT',
    #         DIRECTORY, full_path,
    #         {'chunk_size': self.chunk_size})
    #
    #     super().stage()
    # '''
