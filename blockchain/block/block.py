from time import time
from utility.printable import Printable


class Block(Printable):
    """
    Represent a Block from a Blockchain

    Attributes:
        index        : index of the block
        previous_hash: hash from the previous block
        transactions : transaction info in the block
        proof        : actaul proof of work
        timestamp    : timestamp for actions
    """
    def __init__(
        self, index, previous_hash, transactions, proof, timestamp=time()
    ) -> None:
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = time() if timestamp is None else timestamp
        self.transactions = transactions
        self.proof = proof
