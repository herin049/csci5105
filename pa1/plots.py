from matplotlib import pyplot as plt
from numpy import genfromtxt
import numpy as np

if __name__ == '__main__':
    data = genfromtxt('random.csv', delimiter=',')[1:]
    plt.plot(data[:,0], data[:,1], label='Theoretical')
    plt.plot(data[:,0], data[:,2], label='Observed')
    plt.xlabel('Average load probability')
    plt.ylabel('Average job delay (seconds)')
    plt.legend()
    plt.show()
    plt.savefig('plot_random.png')


    bar_width = 0.25

    random = [2.359, 3.025, 2.84]
    load_balancing = [2.330, 3.037, 2.392]
    
    r1 = np.arange(len(random))
    r2 = [x + bar_width for x in r1]
    
    plt.clf()
    plt.bar(r1, random, color='#557f2d', width=bar_width, edgecolor='white', label='random')
    plt.bar(r2, load_balancing, color='#2d7f5e', width=bar_width, edgecolor='white', label='load balancing')
    
    plt.ylabel('Average job delay (seconds)')
    plt.xticks([r + bar_width for r in range(len(random))], ['low', 'high', 'mixed'])
    
    plt.legend()
    plt.show()
    plt.savefig('bar_chart.png')

