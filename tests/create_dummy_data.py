# this generates some dummy data for the dual channel pizza
# boxes since i dont have access to any data yet
import numpy as np

# test some filename
fname = "/home/xf07bm/.ipython/profile_collection_dev/tests/pb_1chan.txt"
arr = np.loadtxt(fname).astype(int)

with open("pb_2chan.txt", "w") as f:
    for line in arr:
        f.write(f"{line[0]} {line[1]} {line[2]} 0x{line[3]:08x} 0x{line[3]+10:08x}\t\n")



