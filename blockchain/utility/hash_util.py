import json
import hashlib as hl


def hash_string_256(string: str) -> str:
    """
    Generate a unique hash for the input
    string

    Args:
        string: actual input string to
        generate the hash
    """
    return hl.sha256(string).hexdigest()


def hash_block(block: dict) -> str:
    """
    Hashes a block and returns a string representation
    of it

    Args:
        block: block of which the hash is to be generated
    """
    hashable_block = block.__dict__.copy()
    hashable_block["transactions"] = [
        tx.to_ordered_dict() for tx in hashable_block["transactions"]
    ]
    return hash_string_256(json.dumps(hashable_block, sort_keys=True).encode())
    # encode to utf-8 - string format that can be used by sha-256
    # encode() yields binary string - not printable/not readable
    # hexdigest - sha-256 returns a byte hash - to be converted
    # to normal string using hexdigest
