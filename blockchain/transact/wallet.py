import binascii
import Crypto.Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256


class Wallet:
    """
    Represent a Wallet for a node

    Attributes:
        private_key: private key for a node
        public_key : public key for a node
    """
    def __init__(self, node_id) -> None:
        self.private_key = None
        self.public_key = None
        self.node_id = node_id

    def create_keys(self) -> None:
        """
        Get the Public/Private keys
        """
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key

    def save_keys(self) -> bool:
        """
        Save Public/Private keys to a file
        """
        if self.public_key != None and self.private_key != None:
            try:
                with open(f"wallet-{self.node_id}.txt", "w") as file:
                    file.write(self.public_key)
                    file.write("\n")
                    file.write(self.private_key)
                return True
            except (IOError, IndexError):
                print("Saving wallet failed...")
                return False

    def load_keys(self) -> bool:
        """
        Read Public/Private keys from a file
        """
        try:
            with open(f"wallet-{self.node_id}.txt", "r") as file:
                keys = file.readlines()
                public_key = keys[0].strip("\n")
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except (IOError, IndexError):
            print("Loading Wallet failed...")
            return False

    def generate_keys(self) -> tuple:
        """
        Generate Public/Private Keys
        """
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        return (
            binascii.hexlify(private_key.exportKey(format="DER")).decode("ascii"),
            binascii.hexlify(public_key.exportKey(format="DER")).decode("ascii"),
        )

    def sign_transaction(self, sender, recipient, amount) -> str:
        """
        Generate a signature for a transaction

        Args:
            sender: sender of the coins
            recipient: recipient of the coins
            amount: amount of coins
        """
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        h = SHA256.new((str(sender) + str(recipient) + str(amount)).encode("utf-8"))
        signature = signer.sign(h)
        return binascii.hexlify(signature).decode("ascii")

    @staticmethod
    def verify_transaction(transaction) -> str:
        """
        Verify a transaction

        Args:
            transaction: actual transaction object
        """
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new(
            (
                str(transaction.sender) + str(transaction.recipient) + str(transaction.amount)
            ).encode("utf-8")
        )
        return verifier.verify(h, binascii.unhexlify(transaction.signature))
