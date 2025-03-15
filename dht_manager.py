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

# ============== GLOBAL VARIABLES =============== #
client_dictionary = {}  # Global dictionary to store client information
serverSocket = None    # Global socket variable


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

# ============== DHT COMMAND: register =============== #
def register_client(client_message, clientAddress):
    if not check_register_command(client_message):
        logger.error("Registration failed: Invalid command format")  
        return

    command = client_message.split(" ")
    # after error checking, I can add the registered client in the dictionary
    logger.info(f"Successfully registered client: {command[1]}") 
    
    client_dictionary[command[1]] = {command[2], command[3], command[4], client_state.FREE}
    client_response = "SUCCESS"
    
    serverSocket.sendto(client_response.encode(), clientAddress)

# ============== FUNCTION: VALIDATE REGISTRATION COMMAND FORMAT =============== #
def check_register_command(client_message):
    # See if 4 arguments total in register command (register +  4 args)
    command = client_message.split(" ")
    if len(command) != 5:
        logger.warning("Invalid number of arguments")  # Add log
        return False

    # This is all for checking if the register command lines up with the syntax provided
    # The m-port, p-port, and IP address still need to be checked, though

    # This is to check if first argument is register
    if command[0] != "register":
        logger.warning("First argument is not 'register'")  
        return False

    # Then, this is to check that the first command is not greater than 15 in length, not lesser than 1
    # also, to check if it's all alphabetical characters, and if the name isn't in the dictionary
    if len(command[1]) > 15 or len(command[1]) < 1:
        logger.warning(f"Invalid peer name length: {command[1]}")  
        return False
    if not command[1].isalpha():
        logger.warning(f"Peer name not alphabetic: {command[1]}")  
        return False
    if command[1] in client_dictionary:
        logger.warning(f"Peer name already exists: {command[1]}")  
        return False

    if not IP_address_valid(command[2]):
        logger.warning(f"Invalid IP address: {command[2]}")  
        return False

    # the m-port has to be unique from a p-port, and it has to be unique for each process
    if command[3] == command[4]:
        logger.warning(f"m_port and p_port are identical: {command[3]}") 
        return False

    return True

# ============== FUNCTION: VALIDATE IP ADDRESS =============== #
def IP_address_valid(entered_IP_address):
    try:
        ipaddress.ip_address(entered_IP_address)
        return True
    except ValueError:
        return False


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
                pass
            elif "dht-complete" in message:
                # TODO: Implement dht-complete
                pass
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
