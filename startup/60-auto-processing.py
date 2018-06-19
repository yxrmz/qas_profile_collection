print(__file__)
# Things for the ZMQ communication
import socket

PB_PULSES_PER_DEGREE = 23600*400/360

from bluesky.callbacks import CallbackBase

# Needs the lightflow environment
from lightflow.config import Config
from lightflow.workflows import start_workflow

# set where the lightflow config file is
lightflow_config_file = "/home/xf07bm/.config/lightflow/lightflow.cfg"
import socket

def create_interp_request(uid):
    '''
        Create an interpolation request.

    '''
    data = dict()
    requester = str(socket.gethostname())
    request = {
            'uid': uid,
            'pulses_per_deg': PB_PULSES_PER_DEGREE,
            'requester': requester,
            'type': 'spectroscopy',
            'processing_info': {
                'type': 'interpolate',
                'interp_base': 'i0'
            }
        }
    return request 



def submit_lightflow_job(req):
    '''
        Submit an interpolation job to lightflow
        
        uid : the uid of the data set
        lightflow_config : the lightflow config filename
    '''
    config = Config()
    config.load_from_file(lightflow_config_file)

    store_args = dict()
    store_args['request'] = req
    job_id = start_workflow(name='interpolation', config=config,
                            store_args=store_args, queue="qas-workflow")
    print('Started workflow with ID', job_id)

class InterpolationRequester(CallbackBase):
    '''
        The interpolation requester

        On a stop doc, submits request to lightflow
    '''
    def stop(self, doc):
        uid = doc['run_start']
        req = create_interp_request(uid)
        submit_lightflow_job(req)


import sys
sys.path.append("/home/xf07bm/Repos/workflows")
class InterpolationRequesterNoLightFlow(CallbackBase):
    '''
        The interpolation requester

        On a stop doc, submits request to lightflow
    '''
    # NOTE : for testing ONLY
    def stop(self, doc):
        uid = doc['run_start']
        request = create_interp_request(uid)
        #submit_lightflow_job(request)
        store = dict()
        store['request'] = request
        data = dict()
        import interpolation
        interpolation.process_run_func(data, store, None, None)




interpolator = InterpolationRequester()
#interpolator = InterpolationRequesterNoLightFlow()
interpolation_subscribe_id = RE.subscribe(interpolator)
