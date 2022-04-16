import pathlib
import sys
import random
import string

if __name__ == '__main__':
    if len(sys.argv) < 6:
        print('Insufficient number of arguments.')
    num_files = int(sys.argv[1])
    num_writes = int(sys.argv[2])
    num_reads = int(sys.argv[3])
    client_num = int(sys.argv[4])
    file_name = sys.argv[5]

    def gen_str():
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=100))

    files = []
    commands = []
    for i in range(num_files):
        file = f'{client_num}-{i}.txt'
        files.append(file)
        commands.append(f'write {file} {gen_str()}')

    remaining_writes = num_writes
    remaining_reads = num_reads

    while remaining_writes > 0 or remaining_reads > 0:
        p_read = (remaining_reads) / (remaining_writes + remaining_reads)
        file = random.choice(files)
        if random.random() < p_read:
            commands.append(f'read {file}')
            remaining_reads -= 1
        else:
            commands.append(f'write {file} {gen_str()}')
            remaining_writes -= 1

    pathlib.Path(file_name).write_text('\n'.join(commands))