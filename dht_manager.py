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


# ============== CLIENT STATE ENUM =============== #
class client_state(Enum):
    FREE = 1
    LEADER = 2
    INDHT = 3

# ============== DHT COMMAND: register =============== #
def register_client(client_message):
    if not check_register_command(client_message):
        print("FAILURE")
        return

    command = client_message.split(" ")
    # after error checking, I can add the registered client in the dictionary
    client_dictionary[command[1]] = {command[2], command[3], command[4], client_state.FREE}
    print("SUCCESS")
    client_response = "SUCCESS"
    serverSocket.sendto(client_response.encode(), clientAddress)

# ============== FUNCTION: VALIDATE REGISTRATION COMMAND FORMAT =============== #
def check_register_command(client_message):
    # See if 4 arguments total in register command (register +  4 args)
    command = client_message.split(" ")
    if len(command) != 5:
        return False

    # This is all for checking if the register command lines up with the syntax provided
    # The m-port, p-port, and IP address still need to be checked, though

    # This is to check if first argument is register
    if command[0] != "register":
        return False

    # Then, this is to check that the first command is not greater than 15 in length, not lesser than 1
    # also, to check if it's all alphabetical characters, and if the name isn't in the dictionary
    if len(command[1]) > 15 or len(command[1]) < 1:
        print("second length issue")
        return False
    if not command[1].isalpha():
        return False
    if command[1] in client_dictionary:
        return False

    if not IP_address_valid(command[2]):
        return False

    # the m-port has to be unique from a p-port, and it has to be unique for each process
    if command[3] == command[4]:
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
        print("Incorrect Command!")
        print("Usage: python3 dht_manager.py <port>")
        sys.exit(1)

    serverPort = (int(sys.argv[1]))
    
    if serverPort <= 1024 or serverPort > 65535:
        print("Please specify a port address within appropriate bounds")
        sys.exit(1)

    # I will create a UDP socket and bind the IP address and port address together
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('', serverPort))

    client_dictionary = {}

    # The server's terminal will print that it is now listening
    print("The server is listening on port ", serverPort)

    try:
        while True:
            # Accept any connections, and send over the server's welcome message to the client
            message, clientAddress = serverSocket.recvfrom(1024)
            message = message.decode()

            if "register" in message:
                register_client(message)

    except KeyboardInterrupt:
        print("The process has been terminated")

    serverSocket.close()

if __name__ == "__main__":
    main()
