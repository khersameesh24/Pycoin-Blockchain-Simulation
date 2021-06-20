from typing import Any

from transact.wallet import Wallet
from utility.hash_util import hash_string_256, hash_block


class Verification:
    """
    Represent Verifications for transactions 
    and proof of work
    """

    # method - valid_proof() - only works with the inputs its getting
    # and is not accessing anything from the class and hence is a
    # use case for @staticmethod
    @staticmethod
    def valid_proof(transactions, last_hash, proof) -> bool:
        """
        Validate a proof of work and see if it solves the puzzle algorithm

        Args:
            transactions: the transactions of the block for which the proof is calculated
            last_hash: the previous block's hash which will be stored in the next block
            proof: the proof we are testing
        """
        guess = (
            str([tx.to_ordered_dict() for tx in transactions])
            + str(last_hash)
            + str(proof)
        ).encode()
        guess_hash = hash_string_256(guess)
        return guess_hash[0:2] == "00"

    # fn() verify chain accesses valid_proof() method,
    # but an instance of the class in not required and
    # hence is a good use case for @classmethod
    @classmethod
    def verify_chain(cls, blockchain) -> bool:
        """
        Verify the current blockchain and return True 
        if it's valid., False if proof of work is invalid

        Args:
            blockchain: the blockchain to verify
        """
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            if not cls.valid_proof(
                block.transactions[:-1], block.previous_hash, block.proof
            ):
                print("Proof of work is invalid")
                return False
        return True

    # method verify_transaction has no class dependencies
    # and hence is a @static method
    @staticmethod
    def verify_transaction(transaction: dict, get_balance, check_funds=True) -> bool:
        """
        Verify the transaction by checking wether the sender has
        sufficient coins
        Args:
            transaction: transaction that should be cerified
        """
        if check_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(
                transaction
            )
        else:
            return Wallet.verify_transaction(transaction)

    # method - verify transactions has a class dependency on the
    # verify transaction method and hence is a @classmethod
    @classmethod
    def verify_transactions(cls, open_transactions, get_balance) -> Any:
        """
        Verify if all open transactions are legal
        """
        return all(
            [cls.verify_transaction(tx, get_balance, False) for tx in open_transactions]
        )
