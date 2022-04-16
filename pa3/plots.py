from matplotlib import pyplot as plt
from numpy import genfromtxt
import numpy as np

if __name__ == '__main__':
    bar_width = 0.25

    read_heavy = [83.345, 87.668, 94.161, 97.725]
    mixed = [66.318, 57.918, 54.741, 48.475]
    write_heavy = [50.656, 42.516, 36.650, 32.423]

    
    r1 = np.arange(len(read_heavy))
    r2 = [x + bar_width for x in r1]
    r3 = [x + bar_width for x in r2]
    
    plt.clf()
    plt.bar(r1, read_heavy, width=bar_width, edgecolor='white', label='read heavy')
    plt.bar(r2, mixed, width=bar_width, edgecolor='white', label='mixed')
    plt.bar(r3, write_heavy, width=bar_width, edgecolor='white', label='write heavy')
    
    plt.ylabel('Throughput (ops/sec)')
    plt.xlabel('Quorum sizes (read/write)')
    plt.xticks([r + bar_width for r in range(len(read_heavy))], ['4/4', '3/5', '2/6', '1/7'])
    
    plt.legend()
    plt.savefig('bar_chart.png')