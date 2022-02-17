import sys
sys.path.append('gen')

import os
import cv2

from argparse import ArgumentParser
from random import random
from time import sleep

from gen.service.ttypes import Task, TaskRejected

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

class ComputeHandler:
    def __init__(self, input_dir: str, output_dir: str, load_probability: float, load_delay: float, policy: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.load_probability = load_probability
        self.load_delay = load_delay
        self.policy = policy

    def process(self, task: Task) -> None:
        if self.policy == 'random':
            if random() <= self.load_probability:
                sleep(self.load_delay)
        elif self.policy == 'load':
            if random() <= self.load_probability:
                raise TaskRejected("Load exceeded")

        img = cv2.imread(filename=os.path.join(self.input_dir, task.file_name))
        gray = cv2.cvtColor(src=img, code=cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(image=gray, threshold1=100, threshold2=200)
        cv2.imwrite(filename=os.path.join(self.output_dir, task.file_name), img=edges)
        

if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument('-indir', dest='input_dir', default='data/input_dir')
    parser.add_argument('-outdir', dest='output_dir', default='data/output_dir')
    parser.add_argument('-lprob', dest='load_probability', default=0.5)
    parser.add_argument('-ldelay', dest='load_delay', default=3)
    parser.add_argument('-policy', dest='policy', default='random')

    args = parser.parse_args()

    print(args)
    
