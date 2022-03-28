import hashlib
import json

def hash(word, num_bits) -> int:
    return int.from_bytes(hashlib.sha256(word.encode('utf-8')).digest(), 'little', signed=False) % 2 ** num_bits

def inrange(start, end, k) -> bool:
    if k >= start and k <= end:
        return True
    return start >= end and (k >= start or k <= end)

def load_config(config_file) -> dict: 
    with open(config_file, 'r') as file:
        data = file.read()
    return json.loads(data)