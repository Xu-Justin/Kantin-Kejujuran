import os
import config

folder = config.storage_folder
os.makedirs(folder, exist_ok=True)

def get_unique_name(folder='./', prefix='', suffix='', seed=''):
    name = prefix + str(hash(folder + prefix + str(seed) + suffix)) + suffix
    if os.path.exists(os.path.join(folder, name)):
        name = prefix + str(hash(name)) + suffix
    return name