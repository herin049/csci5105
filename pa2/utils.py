import hashlib
import json

# Compute the hash of a word or key by taking the sha256 hash and extracting the lower "num_bits" bits
def hash(word, num_bits) -> int:
    return int.from_bytes(hashlib.sha256(word.encode('utf-8')).digest(), 'little', signed=False) % 2 ** num_bits

# Determines if a key "k" lies in the range "[start, end]" 
def inrange(start, end, k) -> bool:
    if k >= start and k <= end:
        return True
    return start >= end and (k >= start or k <= end)

# Loads the configuration file into a python dictionary
def load_config(config_file) -> dict: 
    with open(config_file, 'r') as file:
        data = file.read()
    return json.loads(data)