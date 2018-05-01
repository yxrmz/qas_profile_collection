import matplotlib
matplotlib.use("Agg")

import numpy as np

from databroker.assets.handlers_base import HandlerBase

from collections import namedtuple

from databroker import Broker
db = Broker.named("qas")



class PizzaBoxAnHandlerTxt(HandlerBase):
    ''' Like pizza box handler except each file has two columns
    '''
    "Read PizzaBox text files using info from filestore."

    def __init__(self, fpath, chunk_size):
        self.chunk_size = chunk_size
        print("chunk size : {}".format(chunk_size))
        with open(fpath, 'r') as f:
            self.lines = list(f)
        print(fpath)
        self.ncols = len(self.lines[0].split())
        print("number of columns is {}".format(self.ncols))
        self.cols = ['ts_s', 'ts_ns', 'index', 'adc']
        self.bases = [10, 10, 10, 16]
        self.encoder_row = namedtuple('encoder_row', self.cols)

    def __call__(self, chunk_num, column_number=0):

        cs = self.chunk_size
        col_index = column_number + 3
        # TODO : clean up this logic, maybe use pandas?
        # need to first look at how isstools parses this
        return [self.encoder_row(*(int(v, base=b) for v, b in zip((ln.split()[i] for i in [0,1,2,col_index]), self.bases)))
                for ln in self.lines[chunk_num*cs:(chunk_num+1)*cs]]



db.reg.register_handler('PIZZABOX_AN_FILE_TXT',       
                        PizzaBoxAnHandlerTxt, overwrite=True)

# test previous data 
'''
uid = "ecf9deed-daed-4d5d-a164-56ab9b9bb42a"
hdr = db[uid]

data = hdr.data('pba1_adc6', stream_name='pba1_adc6')

# test new data
fname = "/home/xf07bm/.ipython/profile_collection_dev/tests/pb_2chan.txt"
# i got this from previous data
chunk_size = 1024
new_han = PizzaBoxAnHandlerTxt(fpath=fname, chunk_size=chunk_size)

chunk_num = 1
res1 = new_han(chunk_num=chunk_num, column_number=0)

chunk_num = 1
res2 = new_han(chunk_num=chunk_num, column_number=1)

print(res1[0].adc)
print(res2[0].adc)
'''
