import os
from dataclasses import dataclass


@dataclass
class AuthenticationKeys:
    alakazam: str
    gengar: str

    KEY_LEN = 36


def get():
    try:
        alakazam_key = os.environb[b'ALAKAZAM_KEY']
        gengar_key = os.environb[b'GENGAR_KEY']
    except KeyError as err:
        raise RuntimeError('Missing authentication keys.') from err
    if len(alakazam_key) != AuthenticationKeys.KEY_LEN or len(gengar_key) != AuthenticationKeys.KEY_LEN:
        raise RuntimeError('Invalid authentication keys.')
    return AuthenticationKeys(alakazam_key, gengar_key)
