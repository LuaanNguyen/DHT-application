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
socket_array = []

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
        print("FAILURE")
        client_response = "FAILURE"
        serverSocket.sendto(client_response.encode(), client_address)
        return

    # set DHT to true, and then continue with setting up DHT
    DHT_set_up = True

    # set up all the commands
    command_args = client_message.split(" ")

    # have to update the remaining number of peers to inDHT and not free

    # first, I'll update the leader's details to LEADER
    leader_details = client_dictionary[command_args[1]]
    leader_details[3] = client_state.LEADER

    # "returning the tuple" really means writing socket details to socket array
    # in other words, I'll be making another socket for each of the peers
    # first, I'll establish the leader at index 0 (the index is their ID)
    socket_array.append((leader_details[0], int(leader_details[2])))
    # socket_array[0].bind((leader_details[0], int(leader_details[2])))

    # now, update n number of users
    curr_count = 1
    for key in client_dictionary:
        if key != command_args[1] and curr_count <= int(command_args[2]):
            print("Initializing other peer sockets")
            client_dictionary[key][3] = client_state.INDHT
            socket_array.append((client_dictionary[key][0], int(client_dictionary[key][2])))
            # socket_array[curr_count].bind((client_dictionary[key][0], int(client_dictionary[key][2])))
            curr_count = curr_count + 1
        elif curr_count > int(command_args[2]):
            break
        else:
            continue

    # brief error checking (seeing if all the states were altered correctly)
    for key in client_dictionary:
        print(key)
        print(client_dictionary[key][3])

    # brief error checking (seeing if the socket_array was initialized properly)
    print(len(socket_array))
    for item in socket_array:
        print(item[1])

    # then return success code
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), client_address)


# ============== DHT COMMAND: register =============== #
def register_client(client_message, clientAddress):
    if not check_register_command(client_message, client_dictionary):
        logger.error("Registration failed: Invalid command format")
        return

    command = client_message.split(" ")
    logger.info(f"Successfully registered client: {command[1]}")

    client_dictionary[command[1]] = [command[2], command[3], command[4], client_state.FREE]
    client_response = "SUCCESS"

    serverSocket.sendto(client_response.encode(), clientAddress)


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
