import json
from .parser import arg


secretsPath = arg('config_file_path')
keys = [
    'activation_bytes',
]


def _updatedSecrets():
    # degenerate function on purpose. the filesystem is weird,
    # but it usually works out in the end, so we fail open.
    try:
        with open(secretsPath, 'r') as file:
            return json.load(file)
    except:
        return {}


def update(key, value):
    """
    Adds key:value pair to config
    Returns updated config
    """
    secrets = _updatedSecrets()
    secrets[key] = value
    with open(secretsPath, 'a') as file:
        file.write(json.dumps(secrets, indent=2))
    return secrets


def get(key):
    """
    find value for given key;
    return empty string if no value found
    """
    try:
        return _updatedSecrets()[key]
    except KeyError:
        return ''


def all():
    """
    returns entire raw config.
    """
    return _updatedSecrets()


def newfile():
    """
    creates a new file with empty values.
    """
    for key in keys:
        update(key, '')


def bytes():
    """
    get activation bytes
    """
    x = arg('abytes')
    return x if x != '' else get('activation_bytes')
