import time
import datetime
import os
import os.path
import uuid
import yaml
import numpy as np
from PIL import Image

from bluesky.callbacks import CallbackBase


class DarkSubtractionCallback(CallbackBase):
    def __init__(self,
                 image_key='pe1_image',
                 primary_stream='primary',
                 dark_stream='dark',
                 db=None,
                 read_path_template='/nsls2/xf07bm/data/pe1_data/%Y/%m/%d/',
                 suffix='.tiff'):
        """Initializes a dark subtraction callback.

        This will perform dark subtraction and then save to file.

        Parameters
        ----------
        image_key : str (optional)
            The detector image string
        primary_stream : str (optional)
            The primary stream name
        dark_stream : str (optional)
            The dark stream name
        db : instance
            A Broker instance
        read_path_template : str (optional)
            A read path template from the tiff plugin of the detector of interest (PE as of time of this writing)
        suffix : str (optional)
            A suffix for the background-subtracted image files
        """

        if db is None:
            raise ValueError("Error, Broker instance (db) is required. Got None")
        self.db = db
        self.pstream = primary_stream
        self.dstream = dark_stream
        self.image_key = image_key
        self.suffix = suffix
        self.read_path_template = read_path_template
        self.clear()

    def start(self, doc):
        self.start_doc = doc 
        self.start_uid = doc['uid']

    def descriptor(self, doc):
        """stash the up and down stream descriptors"""
        if doc['name'] in [self.pstream, self.dstream]:
            self.descriptors[doc['uid']] = doc

    def event(self, doc):
        data_dict = doc['data'] 
        descriptor_uid = doc['descriptor']
        
        stream_name = self.descriptors[descriptor_uid]['name']
        print(f'>>> stream_name: {stream_name}')

        # check it's a prim or dark stream and the key matches the image key desired
        if (stream_name in [self.pstream, self.dstream] and
            self.image_key in doc['data']):
            print(f'>>> Found {self.image_key}')
            event_filled = list(self.db.fill_events([doc], [self.descriptors[descriptor_uid]]))[0]
           
            self.images[stream_name] = event_filled['data'][self.image_key].astype(np.int32)

            # now check if there is an entry in both
            # TODO : Allow for multiple images
            if self.pstream in self.images and self.dstream in self.images:
                print(f'>>> Perform subtraction')
                # Actual subtraction is happening here:
                dsub_image = self.images[self.pstream] - self.images[self.dstream]

                self.clear_images()

                docs = dict()
                docs['start'] = self.start_doc
                docs['descriptor'] = self.descriptors[descriptor_uid].copy()
                # fix to get real stream name in
                docs['descriptor']['name'] = 'bgsub'
                docs['event'] = doc

                dt = datetime.datetime.now()
                dirname = os.path.abspath(dt.strftime(self.read_path_template))
                filepath = os.path.join(dirname, f'{str(uuid.uuid4())}{self.suffix}')
                im = Image.fromarray(dsub_image.astype(np.int32))

                # make sure dir exists
                os.makedirs(dirname, exist_ok=True)

                im.save(filepath)
                print(f'>>> docs: {docs}')

                return docs
            else:
                return doc
        else:
            return doc

    # def save_to_file(self, filename, data):
    #     # TODO : play with mode
    #     im = Image.fromarray(data, mode="I;16")
    #     im.save(filename)
 
    def create_docs(self, data):
        '''        
            Custom doc creation script for bg subbed image.
            Outputs only one image for now.
        '''        
        start_doc = self.start_doc.copy()
        start_doc['uid'] = str(uuid.uuid4())
        start_doc['time'] = time.time()
        print(f'>>> Yielding start: {start_doc}')
        yield ('start', start_doc)

        old_desc = self.descriptors[self.pstream]
        new_desc = dict()
        new_desc['data_keys'] = dict()
        new_desc['data_keys'][self.image_key] = \
            old_desc['data_keys'][self.image_key].copy()
        new_desc['name'] = 'bgsub' 
        new_desc['run_start'] = start_doc['uid']
        new_desc['time'] = time.time()
        new_desc['uid'] = str(uuid.uuid4())
        new_desc['timestamps'] = {self.image_key: time.time}
        print(f'>>> Yielding new_desc: {new_desc}')
        yield ('descriptor', new_desc)

        new_event = dict()
        new_event['data'] = {self.image_key: data}
        new_event['descriptor'] = new_desc['uid']
        # always one event for now
        new_event['seq_num'] = 1
        new_event['time'] = time.time()
        new_event['timestamps'] = {self.image_key : time.time()}
        new_event['uid'] = str(uuid.uuid4())
        print(f'>>> Yielding new_event: {new_event}')
        yield ('event', new_event)

        new_stop = dict()
        new_stop['uid'] = str(uuid.uuid4())
        new_stop['exit_status'] = 'success'
        new_stop['num_events'] = {'bgsub' : 1}
        new_stop['run_start'] = start_doc['uid']
        new_stop['time'] = time.time()
        print(f'>>> Yielding new_stop: {new_stop}')
        yield ('stop', new_stop)

                    
    def clear_images(self):
        self.images = dict()

    def stop(self, doc):
        self.clear()

    def clear(self):
        """Clear the state."""
        self.start_uid = None
        self.start_doc = None
        self.descriptors = dict()
        # TODO : Allow for multiple images
        self.clear_images()


def get_handler(datum_id, db):
    '''Get a file handler from the database.

        datum_id : the datum uid (from db.table() usually...)
        db : the databroker instance (db = Broker.named("pdf") for example)
    '''
    resource = db.reg.resource_given_datum_id(datum_id)
    datums = list(db.reg.datum_gen_given_resource(resource))
    handler = db.reg.get_spec_handler(resource['uid'])
    return handler


def get_file_list(datum_id, db):
    resource = db.reg.resource_given_datum_id(datum_id)
    datums = db.reg.datum_gen_given_resource(resource)
    handler = db.reg.get_spec_handler(resource['uid'])
    datum_kwarg_list = [datum['datum_kwargs'] for datum in datums if datum['datum_id'] == datum_id]
    return handler.get_file_list(datum_kwarg_list)


# Background subtraction callback
bgsub_callback =  DarkSubtractionCallback(image_key="pe1_image",
                                          primary_stream="primary",
                                          dark_stream="dark",
                                          db=db,
                                          read_path_template=pe1c.tiff.read_path_template)

RE.subscribe(bgsub_callback)