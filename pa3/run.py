import os
import pwd
import sys
import signal
from subprocess import Popen
import time

from utils import load_config

def main():
    if len(sys.argv) < 2:
        print('Insufficient number of arguments.')
        return
    run_clients = sys.argv[1] == 'all' or sys.argv[1] == 'clients'
    run_servers = sys.argv[1] == 'all' or sys.argv[1] == 'servers'
    config_file = 'config.json'
    if len(sys.argv) > 2:
        config_file = sys.argv[2]
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

    if run_servers:
        # Start each server
        signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGINT])
        for i, server in enumerate(config['servers']):
            host = server['host']
            print(f'Starting server {i} ({host}).')
            if host == '127.0.0.1':
                processes.append(Popen([python_loc, 'server.py', str(i), config_file]))
            else:
                remote_processes.append((host, 'server.py'))
                ssh_process = Popen(f'ssh {user}@{host} "cd {cwd} && {python_loc} server.py {i} {config_file}"', shell=True)
                processes.append(ssh_process)
        signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGINT])
        print(f'Waiting for servers to boot up...')
        if len(remote_processes) > 0:
            time.sleep(30)
        else:
            time.sleep(5)

    if run_clients:
        # Start each client
        signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGINT])
        for i, client in enumerate(config['clients']):
            host = client['host']
            print(f'Starting client {i} ({host}).')
            if host == '127.0.0.1':
                processes.append(Popen([python_loc, 'client.py', str(i), config_file]))
            else:
                remote_processes.append((host, 'client.py'))
                ssh_process = Popen(f'ssh {user}@{host} "cd {cwd} && {python_loc} client.py {i} {config_file}"', shell=True)
                processes.append(ssh_process)
        signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGINT])
    
    for p in processes:
        p.wait()

    cleanup(None, None)


if __name__ == '__main__':
    main()