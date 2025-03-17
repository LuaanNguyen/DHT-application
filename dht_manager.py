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

# Import validation functions from the new module
from validation_utils import check_register_command, IP_address_valid, check_setupDHT

# ============== GLOBAL VARIABLES =============== #
client_dictionary = {}  # Global dictionary to store client information
serverSocket = None  # Global socket variable
DHT_set_up = False # Global bool to track whether DHT is set up or not
socket_array = [] # List to track peer sockets

# ============== SETTING LOG CONFIGS =============== #
logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Set log message format
    handlers=[
        logging.FileHandler('dht_manager.log'),  # Log to file dht_manager.log
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)


# ============== CLIENT STATE ENUM =============== #
class client_state(Enum):
    FREE = 1
    LEADER = 2
    INDHT = 3
    
# ============== HELPER COMMAND: Print registered peers =============== #
def print_all_peers():
    if len(client_dictionary) <= 0:
        logger.info("No currently registered peers")
        return 
        
    logger.info("Current registered peers:")
    for name, info in client_dictionary.items():
        # Check if info is a dictionary or a list
        if isinstance(info, dict):
            logger.info(f"  - {name}: {info['state']}")
        else:
            # Assuming info is a list with state at index 3
            logger.info(f"  - {name}: {info[3]}")


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


# ============== DHT COMMAND: setupDHT =============== #
def setupDHT(client_message, client_address):
    if not check_setupDHT(client_message, client_dictionary, DHT_set_up):
        logger.warning("Setup DHT failed: Invalid command format")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # set DHT to true, and then continue with setting up DHT
    global DHT_set_up
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
    
    # Select n-1 other peers
    curr_count = 1
    for key in client_dictionary:
        if key != peer_name and curr_count < n:
            logger.info(f"Adding peer {key} to DHT")
            client_dictionary[key]["state"] = client_state.INDHT
            socket_array.append((client_dictionary[key]["ip_addr"], int(client_dictionary[key]["p_port"])))
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
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('', serverPort))
    
    # Log server starting
    print("===== TO EXIT THE PROGRAM, SIMPLY DO CRTL + C =====")
    logger.info(f"Server started on port {serverPort}")

    try:
        while True:
            # Wait for messages from clients
            message, clientAddress = serverSocket.recvfrom(1024)
            message = message.decode()
            logger.info(f"Received message from {clientAddress}: {message}")

            # Handle different commands
            if "register" in message:
                register_client(message, clientAddress)
            elif "setup-dht" in message:
                # TODO: Implement setup-dht
                setupDHT(message, clientAddress)
                pass
            elif "dht-complete" in message:
                # TODO: Implement dht-complete
                pass
            elif "get_neighbor_info" in message:
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
