from asyncio import subprocess
from ctypes.wintypes import POINT
import os
import pwd
import sys
import signal
from subprocess import Popen
import time

from utils import load_config

if __name__ == '__main__':
    # Load the config file
    config_file = 'config.json'
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    config = load_config(config_file)
    user = pwd.getpwuid(os.getuid())[0]

    remote_processes = []
    processes = []
    cwd = os.getcwd()
    python_loc = os.path.join(cwd, 'venv/bin/python')
    global shutting_down
    shutting_down = False

    # Code to kill all the running processes when the program finishes
    def cleanup(sig, frame):
        global shutting_down
        if shutting_down:
            return
        shutting_down = True
        shutdown_processes = []
        if len(processes) > 0:
            print('Shutting down processes...')
            for p in processes:
                p.kill()
        if len(remote_processes) > 0:
            print('Shutting down remote proccesses...')
            for p in remote_processes:
                shutdown_processes.append(Popen(f'ssh {user}@{p[0]} "pkill -f {p[1]}"', shell=True))
            time.sleep(30)
        for p in shutdown_processes:
            p.kill()
        exit(1)

    # Setup SIGINT handler
    signal.signal(signal.SIGINT, cleanup)

    print('Starting the super node.')
    super_node_ip = config['super_node']['ip']
    super_node_port = config['super_node']['port']

    # Start the super node
    if super_node_ip == '127.0.0.1':
        processes.append(Popen([python_loc, 'supernode.py', config_file]))
    else:
        remote_processes.append((super_node_ip, 'supernode.py'))
        ssh_process = Popen(f'ssh {user}@{super_node_ip} "cd {cwd} && {python_loc} supernode.py {config_file}"', shell=True)
        processes.append(ssh_process)

    print('Waiting for super node to start...')
    if len(remote_processes) > 0:
        time.sleep(20)
    else:
        time.sleep(5)

    # Start each of the chord nodes
    for i, node in enumerate(config['chord_nodes']):
        chord_node_ip = node['ip']
        chord_node_port = node['port']
        print(f'Starting chord node {i} ({chord_node_ip}:{chord_node_port}).')
        if chord_node_ip == '127.0.0.1':
            processes.append(Popen([python_loc, 'chordnode.py', str(i), config_file]))
        else:
            remote_processes.append((chord_node_ip, 'chordnode.py'))
            ssh_process = Popen(f'ssh {user}@{chord_node_ip} "cd {cwd} && {python_loc} chordnode.py {i} {config_file}"', shell=True)
            processes.append(ssh_process)
    print('Waiting for DHT to be constructed...')
    if len(remote_processes) > 0:
        time.sleep(len(config['chord_nodes']) * 10)
    else:
        time.sleep(5)

    # Start the client process
    client_process = Popen([python_loc, 'client.py', config_file])
    processes.append(client_process)
    client_process.wait()
    # Run the cleanup logic
    cleanup(None, None)