from flask_cors import CORS
from flask import Flask, jsonify
from flask import request, send_from_directory
from argparse import ArgumentParser

from transact.wallet import Wallet
from block.blockchain import Blockchain

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def get_node_ui():
    """
    Route to the ui(node)
    
    Request: `GET`
    """
    return send_from_directory("ui", "node.html")


@app.route("/network", methods=["GET"])
def get_network_ui():
    """
    Route to the ui(network)

    Request: `GET`
    """
    return send_from_directory("ui", "network.html")


@app.route("/wallet", methods=["POST"])
def create_keys():
    """
    Route to create keys

    Request: `POST`
    """
    wallet.create_keys()
    wallet.save_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            "public_key": wallet.public_key,
            "private_key": wallet.private_key,
            "funds": blockchain.get_balance(),
        }
        return jsonify(response), 201
    else:
        response = {"message": "Saving the keys failed"}
    return jsonify(response), 500


@app.route("/wallet", methods=["GET"])
def load_keys():
    """
    Route to load previously generated keys

    Request: `GET`
    """
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            "public_key": wallet.public_key,
            "private_key": wallet.private_key,
            "funds": blockchain.get_balance(),
        }
        return jsonify(response), 201
    else:
        response = {"message": "Loading the keys failed"}
    return jsonify(response), 500


@app.route("/balance", methods=["GET"])
def get_balance():
    """
    Route to get coin balance

    Request: `GET`
    """
    balance = blockchain.get_balance()
    if balance != None:
        response = {"message": "Fetched Balance Successfully", "funds": balance}
        return jsonify(response), 200
    else:
        response = {
            "message": "Loading balance failed",
            "wallet_set_up": wallet.public_key != None,
        }
        return jsonify(response), 500


@app.route("/broadcast-transaction", methods=["POST"])
def broadcast_transaction():
    """
    Route to broadcast transactions to
    peer nodes

    Request: `POST`
    """
    values = request.get_json()
    if not values:
        response = {"message": "No Data found."}
        return jsonify(response), 400
    required = ["sender", "recipient", "amount", "signature"]
    if not all(key in values for key in required):
        response = {"message": "Some Data is Missing."}
        return jsonify(response), 400
    success = blockchain.add_transaction(
        values["recipient"],
        values["sender"],
        values["signature"],
        values["amount"],
        is_receiving=True,
    )
    if success:
        response = {
            "message": "Successfully added transaction.",
            "transaction": {
                "sender": values["sender"],
                "recipient": values["recipient"],
                "amount": values["amount"],
                "signature": values["signature"],
            },
        }
        return jsonify(response), 201
    else:
        response = {"message": "Creating a transaction failed"}
        return jsonify(response), 500


@app.route("/broadcast-block", methods=["POST"])
def broadcast_block():
    """
    Route to inform peer nodes about
    block additions

    Request: `POST`
    """
    values = request.get_json()
    if not values:
        response = {"message": "No Data found."}
        return jsonify(response), 400
    if "block" not in values:
        response = {"message": "Some Data is Missing."}
        return jsonify(response), 400
    block = values["block"]
    if block["index"] == blockchain.chain[-1].index + 1:
        if blockchain.add_block(block):
            response = {"message": "Block Added"}
            return jsonify(response), 201
        else:
            response = {"message": "Block seems invalid."}
            return jsonify(response), 500
    elif block["index"] > blockchain.chain[-1].index:
        response = {"message": "Blockchain seems to be shorter, block not added."}
        blockchain.resolve_conflicts = True
        return jsonify(response), 200
    else:
        response = {"message": "Blockchain seems to be shorter, block not added"}
        return jsonify(response), 409


@app.route("/transaction", methods=["POST"])
def add_transaction():
    """
    Route to add transactions

    Request: `POST`
    """
    if wallet.public_key == None:
        response = {"message": "No Wallet set up"}
        return jsonify(response), 400
    values = request.get_json()
    if not values:
        response = {"message": "No Data Found!"}
        return jsonify(response), 400
    required_fields = ["recipient", "amount"]
    if not all(field in values for field in required_fields):
        response = {"message": "Required Data is missing."}
        return jsonify(response), 400
    recipient = values["recipient"]
    amount = values["amount"]
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(recipient, wallet.public_key, signature, amount)
    if success:
        response = {
            "message": "Successfully added transaction.",
            "transaction": {
                "sender": wallet.public_key,
                "recipient": recipient,
                "amount": amount,
                "signature": signature,
            },
            "funds": blockchain.get_balance(),
        }
        return jsonify(response), 201
    else:
        response = {"message": "Creating a transaction failed"}
        return jsonify(response), 500


@app.route("/mine", methods=["POST"])
def mine():
    """
    Route to mine a block

    Request: `POST`
    """
    if blockchain.resolve_conflicts:
        response = {"message": "Resolve conflicts first, block not added."}
        return jsonify(response), 409
    block = blockchain.mine_block()
    if block != None:
        dict_block = block.__dict__.copy()
        dict_block["transactions"] = [tx.__dict__ for tx in dict_block["transactions"]]
        response = {
            "message": "Block added successfully",
            "block": dict_block,
            "funds": blockchain.get_balance(),
        }
        return jsonify(response), 201
    else:
        response = {
            "message": "Adding a block failed",
            "wallet_set_up": wallet.public_key != None,
        }
        return jsonify(response), 500


@app.route("/resolve-conflicts", methods=["POST"])
def resolve_conflicts():
    """
    Route to resolve conflicts amongst
    peer nodes

    Request: `POST`
    """
    replaced = blockchain.resolve()
    if replaced:
        response = {"message": "Chain was replaced!"}
    else:
        response = {"message": "Local chain kept!"}
    return jsonify(response), 200


@app.route("/transactions", methods=["GET"])
def get_open_transactions():
    """
    Route to get all open_transactions

    Request = `GET`
    """
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    return jsonify(dict_transactions), 200


@app.route("/chain", methods=["GET"])
def get_chain():
    """
    Route to get a snapshot of a chain

    Request = `GET`
    """
    chain_snapshot = blockchain.get_chain()
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block["transactions"] = [tx.__dict__ for tx in dict_block["transactions"]]
    return jsonify(dict_chain), 200


@app.route("/node", methods=["POST"])
def add_node():
    """
    Route to add a node to the peer
    network

    Request = `POST`
    """
    values = request.get_json()
    if not values:
        response = {"message": "No Data attached"}
        return jsonify(response), 400
    if "node" not in values:
        response = {"message": "No Node Data found"}
        return jsonify(response), 400

    node = values["node"]
    blockchain.add_peer_node(node)
    response = {
        "message": "Node Added Successfully",
        "Nodes": blockchain.get_peer_nodes(),
    }
    return jsonify(response), 201


@app.route("/node/<node_url>", methods=["DELETE"])
def remove_node(node_url):
    """
    Route to remove an invalid node
    from the network

    Args:
        node_url: url of the node to remove
    
    Request = `DELETE`
    """
    if node_url == "" or node_url == None:
        response = {"message": "No Node found"}
        return jsonify(response), 400
    blockchain.remove_peer_node(node_url)
    response = {"message": "Node Removed", "all_nodes": blockchain.get_peer_nodes()}
    return jsonify(response), 200


@app.route("/nodes", methods=["GET"])
def get_nodes():
    """
    Route to get info of all peer
    nodes

    Request = `GET` 
    """
    nodes = blockchain.get_peer_nodes()
    response = {"all_nodes": nodes}
    return jsonify(response), 200


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)
    """Launch the Blockchain App on localhost:5000"""
    app.run(host="0.0.0.0", port=port)
