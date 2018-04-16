'''
import matplotlib
matplotlib.use("Agg")

from databroker.assets.handlers_base import HandlerBase

from databroker import Broker
db = Broker.named("qas")
'''



class PizzaBoxAnHandlerTxt(HandlerBase):
    ''' Like pizza box handler except each file has two columns
    '''
    encoder_row = namedtuple('encoder_row', ['ts_s', 'ts_ns', 'index', 'adc', 'adc2'])
    "Read PizzaBox text files using info from filestore."

    bases = (10, 10, 10, 16)
    def __init__(self, fpath, chunk_size):
        self.chunk_size = chunk_size
        with open(fpath, 'r') as f:
            self.lines = list(f)
        print(fpath)
        self.ncols = len(self.lines[0].split())

    def __call__(self, chunk_num):

        cs = self.chunk_size
        return [self.encoder_row(*(int(v, base=b) for v, b in zip(ln.split(), self.bases)))
                for ln in self.lines[chunk_num*cs:(chunk_num+1)*cs]]


db.reg.register_handler('PIZZABOX_AN_FILE_TXT',       
                        PizzaBoxDualAnHandlerTxt, overwrite=True)
