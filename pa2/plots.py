from matplotlib import pyplot as plt
from numpy import genfromtxt
import numpy as np

if __name__ == '__main__':
    execution_time = [3.3903 , 2.88562]
    operations_per_sec = [180 / e for e in execution_time]
    bars = ('Caching Disabled', 'Caching Enabled')
    y_pos = np.arange(len(bars))

    plt.bar(y_pos, operations_per_sec)
    plt.ylabel('Operations per second')
    plt.xticks(y_pos, bars)
    
    plt.show()
    plt.savefig('caching_chart.png')