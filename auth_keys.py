import os
from dataclasses import dataclass


@dataclass
class AuthenticationKeys:
    cnc: str
    gengar: str

    KEY_LEN = 36


def get():
    try:
        cnc_key = os.environ['CNC_KEY']
        gengar_key = os.environ['GENGAR_KEY']
    except KeyError:
        raise RuntimeError('Missing authentication keys.')
    if len(cnc_key) != AuthenticationKeys.KEY_LEN or len(gengar_key) != AuthenticationKeys.KEY_LEN:
        raise RuntimeError('Invalid authentication keys.')
    return AuthenticationKeys(cnc_key, gengar_key)
