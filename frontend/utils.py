import pickle
from base64 import b64decode


async def deserialize(sequence: str):
    return pickle.loads(b64decode(sequence.encode()))
