from typing import Any
from pprint import pprint

from transact.wallet import Wallet
from block.blockchain import Blockchain
from utility.verification import Verification


class Node:
    """
    Represent a Node from a blockchain

    Attributes:
        wallet: an instance of the wallet class
        blockchain: the actual blockchain
    """
    def __init__(self) -> None:
        self.wallet = Wallet()
        self.blockchain = None
        self.wallet.create_keys()
        self.blockchain = Blockchain(self.wallet.public_key)

    def get_transaction_value(self) -> Any:
        """
        Get transaction credentials from the user
        [recipient(str)/amount(float)]
        """
        tx_recipient = input("Enter the recipient of the transaction : ")
        tx_amount = float(input("Your Transaction amount please : "))
        return (tx_recipient, tx_amount)

    def get_user_choice(self) -> str:
        """
        Get user choice from the command line
        """
        user_input = input("Your choice : ")
        return user_input

    def print_blockchain_elements(self) -> None:
        """
        Print the blockchain to view transactions
        """
        for block in self.blockchain.get_chain():
            pprint("Printing Block")
            pprint(block)
        else:
            pprint("-" * 20)

    def listen_for_input(self) -> None:
        """ 
        the atual user input interface
        """
        waiting_for_input = True

        while waiting_for_input:
            print(
                """Please choose an option
            1 : Add a new transaction
            2 : Mine a new block
            3 : Output the blockchain blocks
            4 : Check transaction validity
            5 : Create wallet
            6 : Load wallet
            7 : Save keys
            q : Quit"""
            )
            print("-" * 30)
            user_choice = self.get_user_choice()
            
            if user_choice == "1":
                tx_data = self.get_transaction_value()
                recipient, amount = tx_data
                signature = self.wallet.sign_transaction(
                    self.wallet.public_key, recipient, amount
                )
                
                if self.blockchain.add_transaction(
                    recipient, self.wallet.public_key, signature, amount=amount
                ):
                    print("Added Transaction")
                else:
                    print("Transaction Failed")
                    print(self.blockchain.get_open_transactions())
            
            elif user_choice == "2":
                if not self.blockchain.mine_block():
                    print("Mining Failed, got not wallet?")
            
            elif user_choice == "3":
                self.print_blockchain_elements()
            
            elif user_choice == "4":

                if Verification.verify_transactions(
                    self.blockchain.get_open_transactions(), self.blockchain.get_balance
                ):
                    print("All transactions are valid")
                else:
                    print("There are invalid transactions")
            
            elif user_choice == "5":
                self.wallet.create_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            
            elif user_choice == "6":
                self.wallet.load_keys()
                self.blockchain = Blockchain(self.wallet.public_key)
            
            elif user_choice == "7":
                self.wallet.save_keys()
            
            elif user_choice == "q":
                print("Quiting!")
                waiting_for_input = False
            
            else:
                print("Invalid Input")

            
            if not Verification.verify_chain(self.blockchain.get_chain()):
                self.print_blockchain_elements()
                print("Invalid Blockchain!")
                break
            print(
                "\nBalance : {} -> {:6.2f} coins\n".format(
                    self.wallet.public_key, self.blockchain.get_balance()
                )
            )
        else:
            print("Exiting!....User Left!")


if __name__ == "__main__":
    node = Node()
    node.listen_for_input()
