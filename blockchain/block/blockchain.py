import json
import requests
from typing import Any
from functools import reduce

from block.block import Block
from transact.wallet import Wallet
from utility.hash_util import hash_block
from transact.transaction import Transaction
from utility.verification import Verification


# Initailize the mining reward
MINING_REWARD: float = 10.0


class Blockchain:
    """
    Represent an entire Blockchain

    Attributes:
        genesis_block    : 1st block in the blockchain
        chain            : the actual blockchain(private)
        open_transactions: list of open transactions(private)
        peer_nodes       : set of unique nodes(private)
        public_key       : unique key generated at a node
        node_id          : unique id from a peer node
        resolve_conflicts: boolean to resolve conflicts
    """

    def __init__(self, public_key, node_id) -> None:
        genesis_block = Block(0, "", [], 100, 0)
        self.__chain = [genesis_block]
        self.__open_transactions = []
        self.__peer_nodes = set()
        self.public_key = public_key
        self.node_id = node_id
        self.resolve_conflicts = False
        self.load_data()

    def get_chain(self) -> list:
        """
        Return a copy of the Blockchain, 
        chain is private and hence should 
        not be manipulated from outside, a 
        copy of which can be used for 
        manipulations.
        """
        return self.__chain[:]

    def get_open_transactions(self) -> list:
        """
        Return a copy of the open_transactions, 
        chain is private and hence should not 
        be manipulated from outside, a copy of 
        which can be used for manipulations.
        """
        return self.__open_transactions[:]

    def load_data(self) -> None:
        """
        Load stored data from disk 
        """
        try:
            with open(f"blockchain-{self.node_id}.txt", mode="r") as file:
                file_content = file.readlines()
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [
                        Transaction(
                            tx["sender"], tx["recipient"], tx["signature"], tx["amount"]
                        )
                        for tx in block["transactions"]
                    ]
                    updated_block = Block(
                        block["index"],
                        block["previous_hash"],
                        converted_tx,
                        block["proof"],
                        block["timestamp"],
                    )
                    updated_blockchain.append(updated_block)
                self.__chain = updated_blockchain

                self.__open_transactions = json.loads(file_content[1][:-1])
                updated_transactions: list = []
                for tx in self.__open_transactions:
                    updated_transaction = Transaction(
                        tx["sender"], tx["recipient"], tx["signature"], tx["amount"]
                    )
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):
            pass

    def save_data(self) -> None:
        """
        Save blockchain data on disk
        """
        try:
            with open(f"blockchain-{self.node_id}.txt", mode="w") as file:
                saveable_chain = [
                    block.__dict__
                    for block in [
                        Block(
                            block_el.index,
                            block_el.previous_hash,
                            [tx.__dict__ for tx in block_el.transactions],
                            block_el.proof,
                            block_el.timestamp,
                        )
                        for block_el in self.__chain
                    ]
                ]
                file.write(json.dumps(saveable_chain))
                file.write("\n")
                saveable_tx = [tx.__dict__.copy() for tx in self.__open_transactions]
                file.write(json.dumps(saveable_tx))
                file.write("\n")
                file.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print("Saving Failed!")

    def proof_of_work(self) -> int:
        """
        Generate a proof of work for the open transactions,
        the hash of the previous block and a random number
        (which is guessed until it fits)
        """
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0

        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self, sender=None) -> float:
        """
        Calculate and return the balance for a participant
        """
        if sender == None:
            if self.public_key == None:
                return None
            participant = self.public_key
        else:
            participant = sender
        tx_sender = [
            [tx.amount for tx in block.transactions if tx.sender == participant]
            for block in self.__chain
        ]
        open_tx_sender = [
            tx.amount for tx in self.__open_transactions if tx.sender == participant
        ]
        tx_sender.append(open_tx_sender)
        amount_sent = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
            if len(tx_amt) > 0
            else tx_sum + 0,
            tx_sender,
            0,
        )
        tx_recipient = [
            [tx.amount for tx in block.transactions if tx.recipient == participant]
            for block in self.__chain
        ]
        amount_received = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
            if len(tx_amt) > 0
            else tx_sum + 0,
            tx_recipient,
            0,
        )
        return amount_received - amount_sent

    def get_last_blockchain_value(self) -> Any:
        """
        Return last value of the current blockchain.
        """
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def add_transaction(
        self, recipient: str, sender, signature, amount: float = 1.0, is_receiving=False
    ) -> bool:
        """
        Append a new value as well as the last blockchain value to
        the blockchain

        Args:
            sender : sender of the coins
            recipient : recipient of the coins
            amount : the amount of coins sent with the trasaction
                        (default = 1.0)
        """
        if self.public_key == None:
            return False
        transaction = Transaction(sender, recipient, signature, amount)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = f"http://{node}/broadcast-transaction"
                    try:
                        response = requests.post(
                            url,
                            json={
                                "sender": sender,
                                "recipient": recipient,
                                "amount": amount,
                                "signature": signature,
                            },
                        )
                        if response.status_code == 400 or response.status_code == 500:
                            print("Transaction Declined, Needs Resolving!")
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False

    def mine_block(self) -> bool:
        """
        Create a new block and add open transactions 
        to it
        """
        if self.public_key == None:
            return None

        last_block = self.__chain[-1]
        hashed_block = hash_block(last_block)

        proof = self.proof_of_work()
        reward_transaction = Transaction("MINING", self.public_key, "", MINING_REWARD)

        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block, copied_transactions, proof)

        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        for node in self.__peer_nodes:
            url = f"http://{node}/broadcast-block"
            converted_block = block.__dict__.copy()
            converted_block["transactions"] = [
                tx.__dict__ for tx in converted_block["transactions"]
            ]
            try:
                response = requests.post(url, json={"block": converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print("Block Declined, Needs Resolving!")
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self, block):
        """
        Add a new block to the Blockchain

        Args:
            block : the block to add
        """
        transactions = [
            Transaction(tx["sender"], tx["recipeint"], tx["signature", tx["amount"]])
            for tx in block["transactions"]
        ]
        proof_is_valid = Verification.valid_proof(
            transactions[:-1], block["previous_hash"], block["proof"]
        )
        hashes_match = hash_block(self.chain[-1]) == block["previous_hash"]
        if not proof_is_valid or not hashes_match:
            return False
        converted_block = Block(
            block["index"],
            block["previous_hash"],
            transactions,
            block["proof"],
            block["timestamp"],
        )
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]
        for itx in block["transactions"]:
            for opentx in stored_transactions:
                if (
                    opentx.sender == itx["sender"]
                    and opentx.recipient == itx["recipient"]
                    and opentx.amount == itx["amount"]
                    and opentx.signature == itx["signature"]
                ):
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print("Item was already removed!")
        self.save_data()
        return True

    def resolve(self):
        """
        Resolve Conflicts amongst nodes
        and give precedense to the longest 
        chain
        """
        winner_chain = self.__chain
        replace = False
        for node in self.__peer_nodes:
            url = f"http://{node}/chain"
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [
                    Block(
                        block["index"],
                        block["previous_hash"],
                        [
                            Transaction(
                                tx["sender"],
                                tx["recipient"],
                                tx["signature"],
                                tx["amount"],
                            )
                            for tx in block["transactions"]
                        ],
                        block["proof"],
                        block["timestamp"],
                    )
                    for block in node_chain
                ]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if (
                    node_chain_length > local_chain_length
                    and Verification.verify_chain(node_chain)
                ):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.__chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

    def add_peer_node(self, node):
        """
        Add a new node to the peer node set.

        Args:
            node: The node URL which should be added.
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """
        Remove a node from the peer node set.

        Args:
            node: The node URL which should be removed.
        """
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        """
        Return a list of all connected peer nodes.
        """
        return list(self.__peer_nodes)
