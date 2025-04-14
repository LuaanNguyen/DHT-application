"""
Project Group 9
Luan Nguyen, Somesh Harshavardhan Gopi Krishna, Sophia Gu, Kyongho Gong
Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi

dht_manager.py
"""
from socket import *
import sys
from enum import Enum
import ipaddress
import logging
import random
import os

# Import validation functions from the new module
from validation_utils import check_register_command, IP_address_valid, check_setupDHT

# ============== GLOBAL VARIABLES =============== #
client_dictionary = {}  # Global dictionary to store client information
participating_peers = {} # Global dictionary to track peers in the DHT
serverSocket = None  # Global socket variable
DHT_set_up = False  # Global bool to track whether DHT is set up or not
socket_array = []  # List to track peer sockets
leave_peer = None
join_peer = None
DHT_fully_initialized = False
initialization_check_count = 0

# ============== SETTING LOG CONFIGS =============== #
logging.basicConfig(
    level=logging.INFO,  # Set logging level
    # ➡️  %(asctime)s - %(levelname)s - %(message)s
    format='►  %(message)s',  # Set log message format 
    handlers=[
        # Log to file dht_manager.log + added 'utf-8' for fixing window error
        logging.FileHandler('dht_manager.log', encoding='utf-8'),
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)


# ============== CLIENT STATE ENUM =============== #
class client_state(Enum):
    FREE = 1  # A peer is able to participate in any capacity
    LEADER = 2  # A peer that leads the construction of the DHT
    INDHT = 3  # A peer that is one of the members of the DHT

# ============== DEREGISTER =============== #
def teardown_complete(client_message, client_address):
    global DHT_set_up, socket_array, participating_peers
    
    # Parse the incoming message to extract the peer name
    command = client_message.split(" ")
    
    if len(command) != 2:
        logger.warning("📜  FORMAT: teardown-complete <peer-name>")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    peer_name = command[1]
    
    # Check if the peer exists in the client dictionary
    if peer_name not in client_dictionary:
        logger.warning(f"❌  Peer {peer_name} not registered")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # Check if the DHT has been set up
    if not DHT_set_up:
        logger.warning(f"❌  DHT has not been set up yet.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # Check if the peer is the leader
    peer_state = client_dictionary[peer_name]["state"]
    if peer_state != client_state.LEADER:
        logger.warning(f"❌  Peer {peer_name} is not the leader. Cannot complete teardown.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return
    
    # If the peer is the leader, update all peers' state to FREE
    logger.info(f"✅  Teardown complete received from leader: {peer_name}")
    
    # Reset all DHT-related data structures
    for key in client_dictionary:
        client_dictionary[key]["state"] = client_state.FREE
    
    # Clear the socket array and participating peers
    socket_array = []
    participating_peers = {}
    
    # Mark DHT as not set up
    DHT_set_up = False
    
    # Log the changes
    logger.info("🧹  All peers reset to FREE state")
    logger.info("🧹  DHT structure cleared")
    print_all_peers()
    
    # Send success response
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), client_address)


def teardown_dht(client_message, client_address):
    global DHT_set_up
    
    # Parse the incoming message to extract the peer name
    command = client_message.split(" ")
    
    if len(command) != 2:
        logger.warning("📜  FORMAT: teardown-dht <peer-name>")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    peer_name = command[1]

    # Check if the peer exists in the client dictionary
    if peer_name not in client_dictionary:
        logger.warning(f"❌  Peer {peer_name} not registered")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # Check if the DHT has been set up before attempting teardown
    if not DHT_set_up:
        logger.warning(f"❌  DHT has not been set up yet.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # Check if the peer is the leader
    peer_state = client_dictionary[peer_name]["state"]
    if peer_state != client_state.LEADER:
        logger.warning(f"❌  Peer {peer_name} is not the leader. Cannot initiate teardown.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return
    
    # If the peer is the leader, acknowledge the teardown request with SUCCESS
    logger.info(f"✅  Teardown initiated by leader: {peer_name}")
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), client_address)
    
    # Log that we're waiting for teardown-complete
    logger.info("⏳  Waiting for teardown-complete message...")


def deregister_peer(client_message, client_address):
    global participating_peers, socket_array
    
    # Parse the incoming message to extract the peer name
    command = client_message.split(" ")
    
    if len(command) != 2:
        logger.warning("📜  FORMAT: deregister <peer-name>")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return False
    
    peer_name = command[1]
    logger.info(f"Processing deregister request for peer: {peer_name}")
    
    # Check if the peer exists in the client dictionary
    if peer_name not in client_dictionary:
        logger.warning(f"❌  Peer {peer_name} not registered")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return False

    # Retrieve the state of the peer
    peer_state = client_dictionary[peer_name]["state"]
    logger.info(f"Current state of {peer_name}: {peer_state}")
    
    # If the peer is in a FREE state, deregistration can proceed
    if peer_state == client_state.FREE:
        # Get peer info for cleanup
        peer_ip = client_dictionary[peer_name]["ip_addr"]
        peer_port = int(client_dictionary[peer_name]["p_port"])
        
        # Remove from client dictionary
        del client_dictionary[peer_name]
        logger.info(f"Removed {peer_name} from client dictionary")
        
        # Remove from participating_peers if present
        if peer_name in participating_peers:
            del participating_peers[peer_name]
            logger.info(f"Removed {peer_name} from participating peers")
        
        # Remove from socket_array if present
        for i, (ip, port) in enumerate(socket_array):
            if ip == peer_ip and port == peer_port:
                socket_array.pop(i)
                logger.info(f"Removed {peer_name} from socket array at position {i}")
                break
        
        logger.info(f"✅  Successfully deregistered peer: {peer_name}")
        client_response = "SUCCESS"
        serverSocket.sendto(client_response.encode(), client_address)
        
        # Display updated peer list
        print_all_peers()
        return True
    else:
        # If the peer is not FREE, deregistration fails
        logger.warning(f"❌  Cannot deregister peer {peer_name}: not in FREE state ({peer_state})")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return False


# ============== QUERY-DHT =============== #
def respond_to_query(client_message, client_address):
    # this is duplicated code from validation_utils (check where the peer is in DHT)
    command = client_message.split(" ")
    if not command[1] in client_dictionary:
        logger.warning(f"Peer {command[1]} not registered")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return False

    # Check if the DHT has been set up first before proceeding
    if not DHT_set_up:
        logger.warning("The DHT has not been set up yet. Set up the DHT before querying.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return False

    # lastly, see if the peer state is free (that means it's not in the DHT)
    curr_peer_state = client_dictionary[str(command[1])]["state"]
    if curr_peer_state == client_state.FREE:
        logger.warning("This peer is not registered.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return False

    # Otherwise, select a random peer that is inside the DHT to start query process

    participating_peers_keys = list(participating_peers.keys())
    initial_peer = random.choice(participating_peers_keys)
    client_response = "SUCCESS"
    # client_response = "SUCCESS " + str(participating_peers[initial_peer])

    client_response = client_response + " " + participating_peers[initial_peer]["ip_addr"]
    client_response = client_response + " " + participating_peers[initial_peer]["p_port"]
    serverSocket.sendto(client_response.encode(), client_address)
    logger.info(f"Successfully randomly selected a peer to start query process: {initial_peer}")

# ============== HELPER COMMAND: Print registered peers =============== #
def print_all_peers():
    if len(client_dictionary) <= 0:
        logger.info("No currently registered peers 💻")
        return

    logger.info("Current registered peers:")
    for name, info in client_dictionary.items():
        # Check if info is a dictionary or a list
        if isinstance(info, dict):
            logger.info(f"  ✅ {name}: {info['state']}")
        else:
            # Assuming info is a list with state at index 3
            logger.info(f"  ✅ {name}: {info[3]}")


# ============== HELPER COMMAND: gets neighbor info =============== #
def get_neighbor_info(message, client_address):
    command = message.split(" ")
    id = int(command[1])
    print("Id is " + str(id))
    ip_address = socket_array[id][0]
    print(ip_address)
    port_number = socket_array[id][1]
    print(port_number)
    print()

    response_message = str(ip_address) + " " + str(port_number)
    serverSocket.sendto(response_message.encode(), client_address)


# ============== DHT COMMAND: setup-dht =============== #
def setup_DHT(client_message, client_address):
    global DHT_set_up

    if not check_setupDHT(client_message, client_dictionary, DHT_set_up):
        logger.warning("Setup DHT failed: Invalid command format")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # set DHT to true, and then continue with setting up DHT
    DHT_set_up = True

    # set up all the commands
    command_args = client_message.split(" ")
    peer_name = command_args[1]
    n = int(command_args[2])

    # Update leader's state
    client_dictionary[peer_name]["state"] = client_state.LEADER

    # Add leader to socket array (index 0)
    leader_info = client_dictionary[peer_name]
    socket_array.append((leader_info["ip_addr"], int(leader_info["p_port"])))
    participating_peers[peer_name] = {
        "ip_addr": client_dictionary[peer_name]["ip_addr"],
        "p_port":client_dictionary[peer_name]["p_port"]
    }

    # Select n-1 other peers
    curr_count = 1
    for key in client_dictionary:
        if key != peer_name and curr_count < n:
            logger.info(f"Adding peer {key} to DHT")
            client_dictionary[key]["state"] = client_state.INDHT
            socket_array.append((client_dictionary[key]["ip_addr"], int(client_dictionary[key]["p_port"])))
            participating_peers[key] = {
                "ip_addr": client_dictionary[key]["ip_addr"],
                "p_port": client_dictionary[key]["p_port"]
            }
            curr_count += 1
        if curr_count >= n:
            break

    # Log DHT setup
    logger.info(f"DHT setup with leader {peer_name} and {n} total peers")
    print_all_peers()

    # Add after parsing command_args
    if len(client_dictionary) < n:
        logger.warning(f"Not enough peers registered. Need {n}, have {len(client_dictionary)}")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # Return success
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), client_address)


# ============== DHT COMMAND: setup-dht =============== #
def dht_complete(client_message, client_address):
    global DHT_set_up, DHT_fully_initialized

    # Parse command
    command = client_message.split(" ")

    # there's an extra space added at the end, so the length should really be 3
    if len(command) != 3:
        logger.warning("Invalid dht-complete format")
        client_response = "FAILURE Invalid Format"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    peer_name = command[2]

    # Validate sender is leader
    if peer_name not in client_dictionary:
        logger.warning(f"Unknown peer {peer_name} sent dht-complete")
        client_response = "FAILURE Unknown Peer"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    if client_dictionary[peer_name]["state"] != client_state.LEADER:
        logger.warning(f"Non-leader peer {peer_name} sent dht-complete")
        client_response = "FAILURE Non-leader Peer"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # Otherwise, mark DHT setup as complete, return success
    logger.info(f"DHT Setup completed by leader {peer_name}")
    DHT_fully_initialized = True
    logger.info(f"✅ DHT fully initialized and ready for queries")
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), client_address)

    # Display ring structure
    display_ring_structure()


# ============== DHT COMMAND: register =============== #
def register_client(client_message, clientAddress):
    if not check_register_command(client_message, client_dictionary):
        logger.error(f"Registration failed from {clientAddress}: Invalid command format")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), clientAddress)
        return

    # parse command
    command = client_message.split(" ")
    peer_name = command[1]
    ip_addr = command[2]
    m_port = command[3]
    p_port = command[4]

    # Check if ports are unique for this IP address
    for name, info in client_dictionary.items():
        if isinstance(info, dict):
            # Dictionary format
            if info["ip_addr"] == ip_addr:
                if info["m_port"] == m_port or info["p_port"] == p_port:
                    logger.warning(f"Registration failed: Ports must be unique per IP address")
                    client_response = "FAILURE"
                    serverSocket.sendto(client_response.encode(), clientAddress)
                    return
        else:
            # List format
            if info[0] == ip_addr:
                if info[1] == m_port or info[2] == p_port:
                    logger.warning(f"Registration failed: Ports must be unique per IP address")
                    client_response = "FAILURE"
                    serverSocket.sendto(client_response.encode(), clientAddress)
                    return

    # If port is unique, store client information
    client_dictionary[peer_name] = {
        "ip_addr": ip_addr,
        "m_port": m_port,
        "p_port": p_port,
        "state": client_state.FREE,
        "address": clientAddress,
    }

    logger.info(f"Successfully registered client: {peer_name} at {ip_addr} with m_port={m_port}, p_port={p_port}.")
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), clientAddress)

    # Log current registered peers
    print_all_peers()

# ============== MANAGER COMMAND: leave-dht =============== #
# 1. check if the peer is in DHT
# 2. if YES then 'SUCESS' + save 'peer name'
# 3. After 1, 2 - only 'dht-rebuilt' command allow
def leave_dht(client_message, client_address):
    global leave_peer, DHT_set_up

    command = client_message.split(" ")
    if len(command) != 2:
        logger.warning("📜  FORMAT: leave-dht <peer-name>")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    peer_name = command[1]

    if not DHT_set_up:
        logger.warning("❌  DHT not set up yet.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    if peer_name not in client_dictionary:
        logger.warning(f"❌  Peer {peer_name} not registered.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    state = client_dictionary[peer_name]["state"]
    if state not in [client_state.LEADER, client_state.INDHT]:
        logger.warning(f"❌  Peer {peer_name} not in DHT.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # Valid leave request
    leave_peer = peer_name
    logger.info(f"✅  Leave request accepted from peer: {peer_name}")
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), client_address)

    # reset-id
    try:
        idx = list(participating_peers.keys()).index(peer_name)
        if idx < len(socket_array) - 1:
            next_ip, next_port = socket_array[idx + 1]
        else:
            next_ip, next_port = socket_array[0]

        reset_msg = f"reset-id {idx} {len(socket_array)} {next_ip} {next_port}"
        peer_ip = client_dictionary[peer_name]["ip_addr"]
        peer_pport = int(client_dictionary[peer_name]["p_port"])
        peer_addr = (peer_ip, peer_pport)
        logger.info(f"📩 Sending reset-id to peer {peer_name} at {peer_addr}: {reset_msg}")
        serverSocket.sendto(reset_msg.encode(), peer_addr)
    except Exception as e:
        logger.error(f"⚠️ Failed to send reset-id: {e}")
    
# ============== MANAGER COMMAND: join-dht =============== #
# 1. check if the peer is FREE
# 2. if YES then 'SUCESS' + save 'peer name'
# 3. After 1, 2 - only 'dht-rebuilt' command allow
def join_dht(client_message, client_address):
    global join_peer, DHT_set_up

    command = client_message.split(" ")
    if len(command) != 2:
        logger.warning("📜  FORMAT: join-dht <peer-name>")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    peer_name = command[1]

    if not DHT_set_up:
        logger.warning("❌  DHT not set up yet.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    if peer_name not in client_dictionary:
        logger.warning(f"❌  Peer {peer_name} not registered.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    state = client_dictionary[peer_name]["state"]
    if state != client_state.FREE:
        logger.warning(f"❌  Peer {peer_name} is already in DHT or is a leader.")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # Valid join request
    join_peer = peer_name
    logger.info(f"✅  Join request accepted from peer: {peer_name}")
    
    # Add peer to socket array and update state
    client_dictionary[peer_name]["state"] = client_state.INDHT
    socket_array.append((client_dictionary[peer_name]["ip_addr"], int(client_dictionary[peer_name]["p_port"])))
    participating_peers[peer_name] = {
        "ip_addr": client_dictionary[peer_name]["ip_addr"],
        "p_port": client_dictionary[peer_name]["p_port"]
    }
    
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), client_address)




# ============== DISPLAY: dht-rebuilt =============== #
def display_ring_structure():
    ring = []
    for peer, info in client_dictionary.items():
        if info["state"] in [client_state.LEADER, client_state.INDHT]:
            ring.append(peer)
    if ring:
        ring_str = " → ".join(ring + [ring[0]])
        logger.info(f"🤖  Current Ring Structure: {ring_str}")

# ============== MANAGER COMMAND: dht-rebuilt =============== #
# 1. check if 'peer name' is equal to LEAVE or JOIN
# 2. if NO then FAIL
# 3. if YES then PEERS re-setting
# 4. After 1, 2 - only 'dht-rebuilt' command allow
def dht_rebuilt(client_message, client_address):
    global leave_peer, join_peer, client_dictionary, socket_array, participating_peers

    command = client_message.split(" ")
    if len(command) != 3:
        logger.warning("📜  FORMAT: dht-rebuilt <peer-name> <new-leader>")
        serverSocket.sendto("FAILURE".encode(), client_address)
        return

    peer_name = command[1]
    new_leader = command[2]

    if peer_name != leave_peer and peer_name != join_peer:
        logger.warning(f"❌  Unauthorized dht-rebuilt sender: {peer_name}")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    if new_leader not in client_dictionary:
        logger.warning(f"❌  Unknown new leader: {new_leader}")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    if new_leader == peer_name:
        logger.warning("❌  Leaving peer cannot be the new leader")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # Update DHT ring structure
    if peer_name == leave_peer:
        # Handle peer leaving
        logger.info(f"🔄  Restructuring ring after {peer_name} left")
        
        # Remove the leaving peer from participating peers and socket array
        if peer_name in participating_peers:
            del participating_peers[peer_name]
        
        # Find and remove the peer from socket_array
        peer_ip = client_dictionary[peer_name]["ip_addr"]
        peer_port = int(client_dictionary[peer_name]["p_port"])
        for i, (ip, port) in enumerate(socket_array):
            if ip == peer_ip and port == peer_port:
                socket_array.pop(i)
                break
        
        # Update the peer's state to FREE
        client_dictionary[peer_name]["state"] = client_state.FREE
        
        # Comment out or remove this line
        # redistribute_data(leaving_peer=peer_name)
        
    elif peer_name == join_peer:
        logger.info(f"🔄  Completing join process for {peer_name}")
        # The peer state was already updated in join_dht
        
        # Comment out or remove this line
        # redistribute_data(joining_peer=peer_name)
    
    # Update the leader
    for name, info in client_dictionary.items():
        if info["state"] == client_state.LEADER:
            info["state"] = client_state.INDHT  # Demote old leader
    
    # Promote new leader
    client_dictionary[new_leader]["state"] = client_state.LEADER
    
    # Reset the leave_peer or join_peer flag
    if peer_name == leave_peer:
        leave_peer = None
    elif peer_name == join_peer:
        join_peer = None
    
    logger.info(f"✅  [ DHT rebuilt ]    New leader: {new_leader}")
    display_ring_structure()
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), client_address)

def update_all_peers_ring_structure():
    """Notify all peers in the DHT about the updated ring structure."""
    try:
        # For each peer in the DHT
        for i, (ip, port) in enumerate(socket_array):
            # Get its right neighbor
            next_i = (i + 1) % len(socket_array)
            next_ip, next_port = socket_array[next_i]
            
            # Send ring update
            update_msg = f"ring-update {i} {len(socket_array)} {next_ip} {next_port}"
            peer_addr = (ip, port)
            logger.info(f"📩 Sending ring update to peer at {peer_addr}: {update_msg}")
            serverSocket.sendto(update_msg.encode(), peer_addr)
    except Exception as e:
        logger.error(f"⚠️ Failed to update peers: {e}")

# ============== MAIN =============== #
def main():
    if len(sys.argv) != 2:
        logger.error("Incorrect number of command line arguments")
        print("Usage: python3 dht_manager.py <port>")
        sys.exit(1)

    try:
        serverPort = int(sys.argv[1])
        if serverPort <= 1024 or serverPort > 65535:
            raise ValueError("Port out of range")
    except ValueError as e:
        logger.error(f"Port error: {str(e)}")
        sys.exit(1)

    # Create UDP socket
    global serverSocket
    serverSocket = socket(AF_INET, SOCK_DGRAM)  # IPv4, UDP
    serverSocket.bind(('', serverPort))

    # Log server starting
    print("✨ =================== DHT Manager =================== ✨")
    print("✨ ===== TO EXIT THE PROGRAM, SIMPLY DO CRTL + C ===== ✨")
    logger.info(f"Server started on port {serverPort}")

    try:
        while True:
            # Wait for messages from clients
            message, clientAddress = serverSocket.recvfrom(1024)
            message = message.decode()
            logger.info(f"Received message from {clientAddress}: {message}")

            # Handle different commands - check for exact command patterns
            command_parts = message.split()
            command = command_parts[0] if command_parts else ""
            
            if command == "deregister":
                deregister_peer(message, clientAddress)
            elif command == "register":
                register_client(message, clientAddress)
            elif command == "setup-dht":
                setup_DHT(message, clientAddress)
            elif command == "dht-complete":
                dht_complete(message, clientAddress)
            elif command == "query-dht":
                respond_to_query(message, clientAddress)
            elif command == "leave-dht":
                leave_dht(message, clientAddress)
            elif command == "join-dht":
                join_dht(message, clientAddress)
            elif command == "dht-rebuilt":
                dht_rebuilt(message, clientAddress)
            elif command == "teardown-complete":
                teardown_complete(message, clientAddress)
            elif command == "teardown-dht":
                teardown_dht(message, clientAddress)
            elif command == "get_neighbor_info":  # Helper command
                get_neighbor_info(message, clientAddress)
            else:
                # Send error response back to client
                error_msg = "Unknown command"
                serverSocket.sendto(error_msg.encode(), clientAddress)
                logger.warning(f"Unknown command received from {clientAddress}")

    except KeyboardInterrupt:
        logger.info("Server shutting down")
    finally:
        serverSocket.close()
        logger.info("Server socket closed")


if __name__ == "__main__":
    main()

# Add function to check if all peers are initialized
def check_dht_initialization():
    """Check if all peers in the DHT are fully initialized"""
    global DHT_fully_initialized, initialization_check_count
    
    if not DHT_set_up or len(participating_peers) == 0:
        return False
    
    initialization_check_count += 1
    logger.info(f"🔍 Checking DHT initialization status (attempt {initialization_check_count})")
    
    # Check if we've already sent data to all peers
    if initialization_check_count >= 5:  # After 5 checks, assume initialization is complete
        DHT_fully_initialized = True
        logger.info("✅ DHT considered fully initialized after multiple checks")
        return True
    
    return DHT_fully_initialized

# Add function to trigger data redistribution
def redistribute_data(leaving_peer=None, joining_peer=None):
    """Trigger data redistribution after a peer joins or leaves"""
    global socket_array, participating_peers
    
    if not DHT_set_up or len(socket_array) <= 1:
        logger.warning("⚠️ Cannot redistribute data: DHT not properly set up")
        return
    
    logger.info("🔄 Initiating data redistribution")
    
    # Find leader peer
    leader_name = None
    for name, info in client_dictionary.items():
        if info["state"] == client_state.LEADER:
            leader_name = name
            break
    
    if not leader_name:
        logger.warning("⚠️ Cannot redistribute data: No leader found")
        return
    
    # Send redistribution command to leader
    leader_info = client_dictionary[leader_name]
    leader_ip = leader_info["ip_addr"]
    leader_port = int(leader_info["p_port"])
    leader_addr = (leader_ip, leader_port)
    
    # Create appropriate message based on join or leave
    if leaving_peer:
        redist_msg = f"redistribute leave {leaving_peer}"
    elif joining_peer:
        redist_msg = f"redistribute join {joining_peer}"
    else:
        redist_msg = "redistribute"
    
    try:
        logger.info(f"📩 Sending redistribution command to leader at {leader_addr}: {redist_msg}")
        serverSocket.sendto(redist_msg.encode(), leader_addr)
    except Exception as e:
        logger.error(f"⚠️ Failed to send redistribution command: {e}")
