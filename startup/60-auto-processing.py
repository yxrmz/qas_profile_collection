import qastools

import numpy as np
import time

from qastools.interpolation import interpolate_and_save
from databroker import Broker
import matplotlib.pyplot as plt

# set up the client
from distributed import Client
from distributed import fire_and_forget
client_address = "xf07bm-ws1:8786"


try:
    print("Found client at {}".format(client_address))
    print("Will send fly scans through post processing")
    client = Client(client_address)
    print("Client info:")
    print(client)
except Exception:
    print("Error could not find client at : {}".format(client_address))
    print("Will not send fly scans through post processing")
    client = None


class CallbackBase:
    def __call__(self, name, doc):
        "Dispatch to methods expecting particular doc types."
        return getattr(self, name)(doc)

    def event(self, doc):
        pass

    def bulk_events(self, doc):
        pass

    def descriptor(self, doc):
        pass

    def start(self, doc):
        pass

    def stop(self, doc):
        pass


from collections import deque

futures_queue = deque()

# TODO : Pass e0 from GUI
class PostProcessingCallback(CallbackBase):
    def __init__(self, client, futures_queue):
        '''
            client : the distributed client
            futures_queue : a queue of computed futures
                which will be also passed to GUI
        '''
        self.client = client
        self.plan_name = None
        self.start_uid = None
        self.futures_queue = futures_queue

    def start(self, doc):
        self.plan_name = doc['plan_name']
        self.start_uid = doc['uid']
        self.md = dict(doc)

    def stop(self, doc):
        # start the post processing
        if self.plan_name == 'execute_trajectory':
            print("(PostProcessingCallback) Processing data uid : {}".format(self.start_uid))
            print("Sending request to dask scheduler...")
            if 'e0' not in self.md:
                print("Warning E0 not in metadata. This may lead to a bad plot.")
            future = self.client.submit(interpolate_and_save,'qas', 'qas-analysis',
                            self.start_uid, mono_name='mono1_enc', pulses_per_degree=None)
            self.futures_queue.append(future)
            #fire_and_forget(future)
            print("Done")
        else:
            print("Ignoring plan {}".format(self.plan_name))
        self.plan_name = None
        self.start_uid = None
        

if client is not None:
    RE.subscribe(PostProcessingCallback(client, futures_queue))
