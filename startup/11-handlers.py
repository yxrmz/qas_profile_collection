from databroker.assets.handlers_base import HandlerBase
import pandas as pd
fc = 7.62939453125e-05
adc2counts = lambda x: ((int(x, 16) >> 8) - 0x40000) * fc \
        if (int(x, 16) >> 8) > 0x1FFFF else (int(x, 16) >> 8)*fc
enc2counts = lambda x: int(x) if int(x) <= 0 else -(int(x) ^ 0xffffff - 1)

class PizzaBoxAnHandlerTxt(HandlerBase):
    def __init__(self, fpath, chunk_size=1024):
        '''
        adds the chunks of data to a list
        '''
        print(fpath)

        chunks = pd.read_csv(fpath, chunksize=chunk_size, 
                          delimiter = " ", header=None)

        self.chunks_of_data = list()
        for i, chunk in enumerate(chunks):
            if i == 0:
                ncols_tot = len(chunk.columns)
                ncols = ncols_tot - 3
                # ncols is additional cols, ncols_tot is ncols + 3
                #print("total columns : {}".format(names))
    
                # now write names for columns
                # for the rest, name them counts0, counts1 etc...
                # create full list of columns
                names =['time (s)', 'time (ns)', 'index']
                names = names + [f'counts{i}' for i in range(ncols)]
                chunk_cols = ['total time (s)', 'index'] + [f'volts{j}' for j in range(ncols)]

            chunk.columns = names
            for j in range(ncols):
                chunk[f'volts{j}'] = chunk[f'counts{j}'].apply(adc2counts)

            chunk['total time (s)'] = chunk['time (s)'] + 1e-9*chunk['time (ns)']
            chunk = chunk[chunk_cols]
            self.chunks_of_data.append(chunk)

    def __call__(self, chunk_num, column=0):
        '''
        returns specified chunk number/index from list of all chunks created
        '''
        result = self.chunks_of_data[chunk_num]
        return result

# TODO : move upstream
class PizzaBoxEncHandlerTxt(HandlerBase):
    encoder_row = namedtuple('encoder_row',
                             ['ts_s', 'ts_ns', 'encoder', 'index', 'state'])
    "Read PizzaBox text files using info from filestore."
    def __init__(self, fpath, chunk_size):
        self.chunk_size = chunk_size
        with open(fpath, 'r') as f:
            self.lines = list(f)

    def __call__(self, chunk_num):
        cs = self.chunk_size
        return [self.encoder_row(*(int(v) for v in ln.split()))
                for ln in self.lines[chunk_num*cs:(chunk_num+1)*cs]]


class PizzaBoxDIHandlerTxt(HandlerBase):
    di_row = namedtuple('di_row', ['ts_s', 'ts_ns', 'encoder', 'index', 'di'])
    "Read PizzaBox text files using info from filestore."
    def __init__(self, fpath, chunk_size):
        self.chunk_size = chunk_size
        with open(fpath, 'r') as f:
            self.lines = list(f)

    def __call__(self, chunk_num):
        cs = self.chunk_size
        return [self.di_row(*(int(v) for v in ln.split()))
                for ln in self.lines[chunk_num*cs:(chunk_num+1)*cs]]


#class PizzaBoxAnHandlerTxt(HandlerBase):
#    ''' Like pizza box handler except each file has two columns
#    '''
#    "Read PizzaBox text files using info from filestore."
#
#    def __init__(self, fpath, chunk_size):
#        self.chunk_size = chunk_size
#        #print("chunk size : {}".format(chunk_size))
#        with open(fpath, 'r') as f:
#            self.lines = list(f)
#        print(fpath)
#        self.ncols = len(self.lines[0].split())
#        print("number of columns is {}".format(self.ncols))
#        self.cols = ['ts_s', 'ts_ns', 'index', 'adc']
#        self.bases = [10, 10, 10, 16]
#        self.encoder_row = namedtuple('encoder_row', self.cols)
#
#    def __call__(self, chunk_num, column=0):
#        cs = self.chunk_size
#        col_index = column + 3
#        # TODO : clean up this logic, maybe use pandas?
#        # need to first look at how isstools parses this
#        return [self.encoder_row(*(int(v, base=b) for v, b in zip((ln.split()[i] for i in [0,1,2,col_index]), self.bases)))
#                for ln in self.lines[chunk_num*cs:(chunk_num+1)*cs]]




db.reg.register_handler('PIZZABOX_AN_FILE_TXT',
                        PizzaBoxAnHandlerTxt, overwrite=True)
db.reg.register_handler('PIZZABOX_ENC_FILE_TXT',
                        PizzaBoxEncHandlerTxt, overwrite=True)
db.reg.register_handler('PIZZABOX_DI_FILE_TXT',
                        PizzaBoxDIHandlerTxt, overwrite=True)
