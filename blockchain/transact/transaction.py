from collections import OrderedDict
from utility.printable import Printable


class Transaction(Printable):
    """
    A transaction which can be added to the block
    in the blockchain.

    Attributes:
        sender: the sender of the coins.
        recipient: the recipient of the coins.
        signature: the signature of the transaction.
        amount: the amount of coins sent.
    """

    def __init__(self, sender: str, recipient: str, signature: str, amount: float):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature

    def to_ordered_dict(self):
        """
        Return the sender, recipient &
        amount as elements of an
        ordered dictionary
        """
        return OrderedDict(
            [
                ("sender", self.sender),
                ("recipient", self.recipient),
                ("amount", self.amount),
            ]
        )
