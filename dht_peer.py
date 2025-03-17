"""
Project Group 9
Luan Nguyen, Somesh Harshavardhan Gopi Krishna, Sophia Gu, Kyongho Gong
Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi

dht_manager.py
"""

from socket import*
import sys
import select
import logging

# ============== GLOBAL VARIABLES FOR A PEER =============== #
id = -1
right_neighbor = None
ring_size = -1
socket_array = []
input_file = ""

# ============== SETTING LOG CONFIGS =============== #
logging.basicConfig(
    level=logging.INFO, # Setting logging level
    format='%(asctime)s - %(levelname)s - %(message)s', # Setting log message format
    handlers=[
        logging.FileHandler('dht_peer.log'), # Log to a file
        logging.StreamHandler() # Log to console
    ]
)

def count_line(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    return len(lines) - 1


def check_udp_data(sock):
    """Checks if a UDP socket has data available to read."""
    ready_sockets, _, _ = select.select([sock], [], [], 0)
    return bool(ready_sockets)


def assign_id():
    for i in range(1, ring_size):
        print("In progress")
        if i == ring_size - 1:
            print(ring_size - 1)
            peer_query = "get_neighbor_info " + str(i)
            clientSocket.send(peer_query.encode())
            response_message = clientSocket.recv(2048).decode()
            peer_info = response_message.split(" ")
            peer_ip_address = peer_info[0]
            print(peer_ip_address)
            peer_port = int(peer_info[1])
            print(peer_port)

            peer_neighbor_ip_address = peer_socket.getsockname()[0]
            peer_neighbor_port = int(peer_socket.getsockname()[1])

            response = str(i) + " " + str(ring_size) + " " + str(peer_neighbor_ip_address) + " " + str(
                peer_neighbor_port)
            peer_socket.sendto(response.encode(), (peer_ip_address, peer_port))

        else:
            # get every information on the peer to send them a message
            peer_query = "get_neighbor_info " + str(i)
            clientSocket.send(peer_query.encode())
            response_message = clientSocket.recv(2048).decode()
            peer_info = response_message.split(" ")
            peer_ip_address = peer_info[0]
            peer_port = int(peer_info[1])

            peer_neighbor_query = "get_neighbor_info " + str((i + 1) % (ring_size))
            clientSocket.send(peer_neighbor_query.encode())
            peer_neighbor = receivedMessage.split(" ")
            peer_neighbor_ip_address = peer_neighbor[0]
            peer_neighbor_port = int(peer_neighbor[1])

            response = str(i) + " " + str(ring_size) + " " + str(peer_neighbor_ip_address) + " " + str(peer_neighbor_port)
            peer_socket.sendto(response.encode(), (peer_ip_address, peer_port))
    print("FINISHED")


def main(): 
    if len(sys.argv) != 3:
        print("Incorrect Command!")
        print("Usage: python3 dht_peer.py <manager_ip> <manager_port>")
        sys.exit(1)

    # define the server name and port for the client to connect to
    serverName = sys.argv[1]
    serverPort = int(sys.argv[2])

    # create a UDP client socket, and connect to the server via its IP address and port address
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.connect((serverName, serverPort))
    peer_socket = None

    while True:
        # if the peer socket has been initialized, we can check if it's received a message
        if peer_socket != None and check_udp_data(peer_socket):
            data, addr = peer_socket.recvfrom(1024)
            print(f"Received data: {data} from {addr}")
            data = data.decode()
            mult_response = data.split(" ")
            id = int(mult_response[0])
            ring_size = int(mult_response[1])
            right_neighbor_id = (id + 1) % ring_size
            right_neighbor = (right_neighbor_id, mult_response[2], int(mult_response[3]))
        else:
            print("No data available")

        # query the client to send in an input message and send it
        message = input("Type in a message (type exit to terminate the connection):")
        clientSocket.send(message.encode())

        # if the message is exit, exit the loop
        if message == "exit":
            break

        # if the message contains setup-dht, then the process is the leader
        # I will need to add error checking later
        if "register" in message:
            receivedMessage = clientSocket.recv(2048).decode()
            print(receivedMessage)
            if receivedMessage == "SUCCESS":
                command = message.split(" ")
                peer_socket = socket(AF_INET, SOCK_DGRAM)
                peer_socket.bind((command[2], int(command[4])))
                peer_socket.settimeout(1)

        if "setup-dht" in message:
            receivedMessage = clientSocket.recv(2048).decode()
            print(receivedMessage)
            if receivedMessage == "SUCCESS":
                # set up global variables of the leader
                command = message.split(" ")
                id = 0
                ring_size = int(command[2])
                
                # we know what year of weather records we want, so alter your input file
                year = str(command[3])
                input_file = "details-" + year + ".csv"
                
                # this is to get the information on right neighbor of leader
                right_neighbor_id = (id + 1) % ring_size
                query = "get_neighbor_info " + str(right_neighbor_id)
                clientSocket.send(query.encode())
                receivedMessage = clientSocket.recv(2048).decode()

                # now set up the information of the right neighbor and bind the peer socket
                neighbor_info = receivedMessage.split(" ")
                neighbor_ip_address = neighbor_info[0]
                neighbor_port = int(neighbor_info[1])
                
                # the print statements below are testing junk
                print(neighbor_info[0])
                print(neighbor_info[1])

                right_neighbor = (right_neighbor_id, neighbor_ip_address, neighbor_port)
        
                # set up your ring
                assign_id()
    print("Now exiting the program...")
    
if __name__ == "__main__":
    main()
    
