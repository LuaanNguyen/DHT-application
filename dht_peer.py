"""
Project Group 9
Luan Nguyen, Somesh Harshavardhan Gopi Krishna, Sophia Gu, Kyongho Gong
Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi

dht_peer.py

Test
"""
from socket import *
import sys
import select
import logging
from sympy import *
import csv
import random

# ============== SETTING LOG CONFIGS =============== #
logging.basicConfig(
    level=logging.INFO,
    format='►  %(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # Log to file dht_peer.log + added 'utf-8' for fixing window error
        logging.FileHandler('dht_peer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============== GLOBAL VARIABLES =============== #
peer_name = ""
id = -1
right_neighbor = None
ring_size = -1
DHT = []
DHT_size = -1
input_file = ""

# teardown will just erase all the details stored in the client process about the DHT
def teardown():
    global ring_size
    global id
    global DHT
    global DHT_size
    global input_file
    global right_neighbor

    if id == ring_size - 1:
        ring_size = -1
        id = -1
        DHT = []
        DHT_size = -1
        input_file = ""
        client_message = "Leader: all DHT entries deleted"
        peer_socket.sendto(client_message.encode(), (right_neighbor[1], int(right_neighbor[2])))
        right_neighbor = None
    else:
        ring_size = -1
        id = -1
        DHT = []
        DHT_size = -1
        input_file = ""
        client_message = "peer-teardown"
        peer_socket.sendto(client_message.encode(), (right_neighbor[1], int(right_neighbor[2])))
        right_neighbor = None


def start_search_process(start_ip_addr, start_p_port, event_id, unvisited_ids, id_seq):
    print("Entered search process...")
    if start_ip_addr == peer_socket.getpeername[0]:
        print("Search successfully at the current peer making a query")
        find_pos = calculate_pos(event_id)
        find_id = calculate_id(find_pos)

        if find_id == id:
            search_record = DHT[find_pos]
            if search_record == None:
                print("The record was not found at node " + str(id))
            elif int(search_record[0]) != event_id:
                print("The record was not found at node " + str(id))
            else:
                print("SUCCESSFULLY FOUND THE STORM WITH EVENT_ID: " + str(search_record))
        else:
            id_seq.append(id)
            unvisited_ids.remove(id)
            find_event(event_id, unvisited_ids, id_seq)
    else:
        print("Passing along the query")
        start_message = "start-query " + str(event_id)
        peer_socket.sendto(start_message, (start_ip_addr, start_p_port))


def pass_event_along(event_id, unvisited_ids, id_seq):
    next_contact_node = find_random_node(unvisited_ids, id_seq)
    message = "find_event " + str(event_id) + " " + "unvisit"
    for i in unvisited_ids:
        message = message + " " + str(i)

    message = message + " id_seq"
    for i in id_seq:
        message = message + " " + str(i)

    print("Passing the event along..." + message)

    peer_query = f"get_neighbor_info {next_contact_node}"
    clientSocket.send(peer_query.encode())
    response_message = clientSocket.recv(2048).decode()

    if "FAILURE" in response_message:
        logger.error(f"⚠️ Failed to get info for peer {next_contact_node}")
        return

    peer_info = response_message.split(" ")
    peer_ip_address = peer_info[0]
    peer_port = int(peer_info[1])

    peer_socket.sendto(message, (peer_ip_address, peer_port))


# find-event is going to forward the query request hot-potato style to other peers
def find_event(event_id, unvisited_ids, id_seq):
    find_pos = calculate_pos(event_id)
    find_id = calculate_id(find_pos)

    # find id == global id, we're in luck, because we can just check the DHT stored locally
    if find_id == id:
        search_record = DHT[find_pos]

        # there's 3 possibilities: there exists a record there that matches, no record, or record that doesn't match
        if search_record == None:
            print("The record was not found at node " + str(id))
        elif int(search_record[0]) != event_id:
            print("The record was not found at node " + str(id))
        elif int(search_record[0]) == event_id:
            print("The record was found at node " + str(id))
            # after we find the node, I am going to package it up and send it to the manager
            send_record = "SUCCESS " + search_record.encode()

            clientSocket.send(send_record)
        else:
            print("Unaccounted possibility")

    else:
        # otherwise, we're going to consult visited ID's and find a random node to send to
        print("In progress")

        next_contact_node = find_random_node(unvisited_ids, id_seq)

        # by how I defined find_random_node, if -1 is returned, we've searched all nodes, found nothing
        if next_contact_node == -1:
            # the failure message is going to be sent to the server
            fail_message = "FAILURE, finished searching all nodes"
            clientSocket.send(fail_message)
        else:
            peer_query = f"get_neighbor_info {next_contact_node}"
            clientSocket.send(peer_query.encode())
            response_message = clientSocket.recv(2048).decode()

            if "FAILURE" in response_message:
                logger.error(f"⚠️ Failed to get info for peer {next_contact_node}")
                return

            # here's the message I'm going to send to the peer
            message = "find_event " + str(event_id) + " " + str(unvisited_ids) + " " + str(id_seq)

            peer_info = response_message.split(" ")
            peer_ip_address = peer_info[0]
            peer_port = int(peer_info[1])

            # now, with the peer's info, I'm going to send the request
            peer_socket.sendto(message, (peer_ip_address, peer_port))



def find_random_node(unvisited_ids, id_seq):
    # first, I'm going to add the current ID to the ID_seq
    id_seq.append(id)

    # and then, I'm going to remove id from unvisited ids
    unvisited_ids.remove(id)

    # if the unvisited_ids is empty...we've checked everything, so return special value -1
    if unvisited_ids.empty():
        return -1

    # and then, I'm going to find the next node to contact
    return random.choice(unvisited_ids)

# store_leader is going to initialize the storing process
def store_leader(filename):
    '''Read the CSV file'''
    fields = []
    rows = []
    # reading csv file
    with open(filename, 'r') as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)

        # extracting field names through first row
        fields = next(csvreader)

        # extracting each data row one by one
        for row in csvreader:
            rows.append(row)

    # I'm leaving in this print function, just in case anybody wants to see the process (and also for me)
    '''for row in rows:
        # parsing each column of a row
        for col in row:
            print("%10s" % col, end=" "),
        print('\n')
    for row in rows:
        print(str(row))'''

    set_DHT_size(count_line(input_file))

    # now go through each of the data records and start DHT population
    for row in rows:
        forward_record(row)

    # Probably need a more refined logger function; this just for me and error checking
    print("FINISHED POPULATING THE DHT")


def forward_record(record):

    # all error handling/debugging
    '''print(record[0])
    print(record[1])
    print(record[2])
    print(record[3])
    print(record[4])
    print(record[5])'''
    event_id = int(record[0])
    pos = calculate_pos(event_id)
    node_id = calculate_id(pos)
    print("The record should be stored at node " + str(node_id))
    print("The record should be stored at position " + str(pos))


    # print("The event_id is " + str(event_id))

    # if node_id == id, we're supposed to store the record at the current peer
    if node_id == id:
        # print("Error in the if")
        DHT[pos] = record
        # Note to self: make sure to log this interaction, in a neat manner, rather than messy print statements
        feedback = "Record with event_id " + str(record[0]) + " stored at node " + str(id) + " at pos " + str(pos)
        print(feedback)
        return 0

    # Otherwise, we have to send the record to our next neighbor
    right_neighbor_ip_addr = right_neighbor[1]
    right_neighbor_port = right_neighbor[2]

    # print("Error outside the if")
    # okay, I'm gonna reformat the record...so that it's easier to send as a message
    # print(len(record))
    string_record = str(record[0])
    for item in record[1:]:
        string_record = string_record + " " + str(item)

    request = "store " + str(DHT_size) + " " + string_record + " END"
    peer_socket.sendto(request.encode(), (right_neighbor_ip_addr, right_neighbor_port))

    return 0


# calculate_id will calculate the node at which to store the weather record
def calculate_id(pos):
    return pos % ring_size


# Calculate pos will calculate the position in the local hash table to store record
def calculate_pos(event_id):
    global DHT_size
    return event_id % DHT_size


# The DHT has to be the closest prime number greater than 2 * entries in CSV file
def set_DHT_size(line_count):
    start = (line_count * 2) + 1

    while not isprime(start):
        start = start + 1

    global DHT
    global DHT_size
    DHT = [None] * start
    DHT_size = start


# Counts the number of entries stored in the CSV file
def count_line(filename):
    """Count the number of lines in a file (excluding header)"""
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        return len(lines) - 1  # Subtract 1 for header
    except FileNotFoundError:
        logger.error(f"⚠️ File not found: {filename}")
        return 0
    except Exception as e:
        logger.error(f"⚠️ Error reading file: {e}")
        return 0


def check_udp_data(sock):
    """Checks if a UDP socket has data available to read."""
    if sock is None:
        return False
    try:
        ready_sockets, _, _ = select.select([sock], [], [], 0)
        return bool(ready_sockets)
    except Exception as e:
        logger.error(f"⚠️ Error checking socket: {e}")
        return False


def assign_id():
    """Assign IDs to all peers in the ring"""
    logger.info("Assigning IDs to peers...")
    for i in range(1, ring_size):
        logger.info(f"Setting up peer with ID {i}")

        if i == ring_size - 1:
            # Last peer in the ring
            # Changed to id instead
            peer_query = f"get_neighbor_info {i}"
            clientSocket.send(peer_query.encode())
            response_message = clientSocket.recv(2048).decode()

            if "FAILURE" in response_message:
                logger.error(f"⚠️ Failed to get info for peer {i}")
                continue

            peer_info = response_message.split(" ")
            peer_ip_address = peer_info[0]
            peer_port = int(peer_info[1])

            # For the last peer, its right neighbor is the leader (ID 0)
            # Get our own IP and port for the neighbor info
            try:
                peer_neighbor_ip_address = peer_socket.getsockname()[0]
                peer_neighbor_port = int(peer_socket.getsockname()[1])

                response = f"{i} {ring_size} {peer_ip_address} {peer_neighbor_port}"
                logger.info(f"📩 Sending to peer {i}: {response}")
                peer_socket.sendto(response.encode(), (peer_ip_address, peer_port))

            except Exception as e:
                logger.error(f"⚠️ Error setting up peer {i}: {e}")

        else:
            # Middle peers in the ring
            # Get current peer info
            peer_query = f"get_neighbor_info {i}"
            clientSocket.send(peer_query.encode())
            response_message = clientSocket.recv(2048).decode()

            if "FAILURE" in response_message:
                logger.error(f"⚠️ Failed to get info for peer {i}")
                continue

            peer_info = response_message.split(" ")
            peer_ip_address = peer_info[0]
            peer_port = int(peer_info[1])

            # Get next peer info (right neighbor)
            peer_neighbor_query = f"get_neighbor_info {(i + 1) % ring_size}"
            clientSocket.send(peer_neighbor_query.encode())
            neighbor_response = clientSocket.recv(2048).decode()

            if "FAILURE" in neighbor_response:
                logger.error(f"⚠️ Failed to get info for neighbor {(i + 1) % ring_size}")
                continue

            peer_neighbor = neighbor_response.split(" ")
            peer_neighbor_ip_address = peer_neighbor[0]
            peer_neighbor_port = int(peer_neighbor[1])

            # Send ID and neighbor info to peer
            response = f"{i} {ring_size} {peer_neighbor_ip_address} {peer_neighbor_port}"
            logger.info(f"📩 Sending to peer {i}: {response}")
            peer_socket.sendto(response.encode(), (peer_ip_address, peer_port))

    logger.info("✅ Finished assigning IDs to all peers")

    # Now we are going to set up the DHT for each peer
    store_leader(input_file)

    # Signal completion to manager
    dht_complete_message = f"✅ dht-complete {peer_name}"
    logger.info(f"📩 Sending dht-complete to manager: {dht_complete_message}")

    # for error checking
    print("The peer name is " + peer_name)
    clientSocket.send(dht_complete_message.encode())
    completion_response = clientSocket.recv(2048).decode()
    logger.info(f"✅ DHT completion response: {completion_response}")

    return "SUCCESS" in completion_response


# ============== MAIN =============== #
def main():
    global clientSocket, peer_socket, id, ring_size, right_neighbor, input_file, peer_name, DHT_size

    if len(sys.argv) != 3:
        logger.error("⚠️ Incorrect number of command line arguments")
        print("📜 Usage: python3 dht_peer.py <manager_ip> <manager_port>")
        sys.exit(1)

    # define the server name and port for the client to connect to
    serverName = sys.argv[1]
    try:
        serverPort = int(sys.argv[2])
        if serverPort <= 1024 or serverPort > 65535:
            raise ValueError("Port out of range")
    except ValueError as e:
        logger.error(f"⚠️ Invalid port number: {e}")
        sys.exit(1)

    # create a UDP client socket, and connect to the server via its IP address and port address
    print("✨ =================== DHT Peer ====================== ✨")
    print("✨ ===== TO EXIT THE PROGRAM, SIMPLY DO CRTL + C ===== ✨")
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.connect((serverName, serverPort))
    logger.info(f"✅ Connected to manager at {serverName}:{serverPort}")

    peer_socket = None

    # Instructions
    print("✨ ---------------- Available commands ----------------- ✨")
    print("  ✅ register 〈peer-name〉 〈IPv4-address〉 〈m-port〉 〈p-port〉")
    print("  ✅ setup-dht 〈peer-name〉 〈n〉 〈YYYY〉")
    print("  ✅ dht-complete 〈peer-name〉")
    print("  ✅ query-dht <peer-name>")
    print("  ✅ leave-dht <peer-name>")
    print("  ✅ join-dht <peer-name>")
    print("  ✅ dht-rebuilt <peer-name> <new-leader>")
    print("  ✅ teardown-dht <peer-name>")
    print("  ✅ teardown-complete <peer-name>")
    print("  ✅ deregister <peer-name>")
    print("  ✅ exit")
    print("✨ ----------------------------------------------------- ✨")

    try:
        while True:
            '''Slight usability issue: the peer port is stuck behind the terminal prompt asking
            for an input (completely my fault, my bad). I'm wondering if there's a way to interrupt
            the terminal input prompt as soon as the peer port has something...'''
            # if the peer socket has been initialized, we can check if it's received a message
            if peer_socket is not None and check_udp_data(peer_socket):
                try:
                    data, addr = peer_socket.recvfrom(1024)
                    data_str = data.decode()
                    logger.info(f"Received data from {addr}: {data_str}")
                    mult_response = data_str.split(" ")

                    # Process the peer message

                    if "find_event" in data_str:
                        print(data_str)
                        for i in data_str:
                            print(i)
                    elif "teardown" in data_str:
                        print(data_str)
                        teardown()

                        # This is for checking everything has been destroyed correctly
                        print("Ring size: " + str(ring_size))
                        print("DHT_size: " + str(DHT_size))
                        print("Input file: " + "<" + str(input_file) + ">")
                    elif "Leader" in data_str:
                        client_response = "teardown-complete " + peer_name
                        clientSocket.send(client_response.encode())

                        received_message = clientSocket.recv(2048).decode()
                        logger.info(f"📩 Received from manager: {received_message}")
                        print(received_message)

                    elif "store" in data_str:
                        # we can initialize the DHT now
                        # global DHT_size
                        global DHT
                        if DHT_size == -1:
                            print(mult_response[2:16])
                            DHT_size = int(mult_response[1])
                            print("DHT size: " + str(DHT_size))
                            DHT = [None] * DHT_size

                        curr_record = mult_response[2:16]
                        forward_record(curr_record)
                    elif "start-query" in data_str:

                        query_event_id = int(mult_response[1])
                        nonvisit_ids = []
                        search_process = []
                        for i in range(ring_size):
                            nonvisit_ids.append(i)

                        start_search_process(peer_socket.getpeername()[0], peer_socket.getpeername()[1], query_event_id, nonvisit_ids, search_process)
                    else:
                        if len(mult_response) >= 4:
                            global right_neighbor
                            id = int(mult_response[0])
                            ring_size = int(mult_response[1])
                            right_neighbor_id = (id + 1) % ring_size
                            right_neighbor = (right_neighbor_id, mult_response[2], int(mult_response[3]))
                            logger.info(f"Set peer ID to {id}, ring size to {ring_size}")
                            logger.info(
                                f"Right neighbor: ID={right_neighbor_id}, IP={mult_response[2]}, Port={mult_response[3]}")

                except Exception as e:
                    logger.error(f"⚠️ Error processing peer message: {e}")

            # query the client to send in an input message and send it
            message = input("Type in a message (type exit to terminate and other key to check the peer port): ")

            # if the message is exit, exit the loop
            if message == "exit":
                logger.info("🤖 User requested exit")
                break

            # Send message to manager
            try:
                clientSocket.send(message.encode())
                logger.info(f"📩 Sent to manager: {message}")
            except Exception as e:
                logger.error(f"⚠️ Error sending to manager: {e}")
                continue

            # Process different commands
            try:
                if "register" in message and "deregister" not in message:
                    # Handle register command
                    receivedMessage = clientSocket.recv(2048).decode()
                    logger.info(f"📩 Received from manager: {receivedMessage}")
                    print(receivedMessage)

                    if "SUCCESS" in receivedMessage:
                        command = message.split(" ")
                        peer_name = command[1]  # Store peer name

                        # Create peer socket for P2P communication
                        try:
                            peer_socket = socket(AF_INET, SOCK_DGRAM)
                            # Bind to all interfaces with the p_port
                            peer_socket.bind(('', int(command[4])))
                            logger.info(f"Peer socket bound to port {command[4]}")
                        except Exception as e:
                            logger.error(f"⚠️ Error binding peer socket: {e}")
                            peer_socket = None
                elif "deregister" in message:
                    receivedMessage = clientSocket.recv(2048).decode()
                    logger.info(f"📩 Received from manager: {receivedMessage}")
                    print(receivedMessage)

                    if "SUCCESS" in receivedMessage:
                        print("Now terminating this client process...")
                        sys.exit(1)

                elif "setup-dht" in message:
                    # Handle setup-dht command
                    receivedMessage = clientSocket.recv(2048).decode()
                    logger.info(f"📩 Received from manager: {receivedMessage}")
                    print(receivedMessage)

                    if "SUCCESS" in receivedMessage:
                        # Parse command
                        command = message.split(" ")
                        peer_name = command[1]  # Store peer name

                        # Set leader state
                        id = 0
                        ring_size = int(command[2])

                        # Set up data file
                        year = str(command[3])
                        input_file = f"details-{year}.csv"
                        logger.info(f"Using data file: {input_file}")

                        # Get right neighbor info
                        right_neighbor_id = (id + 1) % ring_size
                        query = f"get_neighbor_info {right_neighbor_id}"
                        logger.info(f"ℹ️ Getting neighbor info: {query}")

                        clientSocket.send(query.encode())
                        receivedMessage = clientSocket.recv(2048).decode()
                        logger.info(f"Neighbor info response: {receivedMessage}")

                        # Parse neighbor info
                        neighbor_info = receivedMessage.split(" ")
                        if len(neighbor_info) >= 2:
                            neighbor_ip_address = neighbor_info[0]
                            neighbor_port = int(neighbor_info[1])

                            # Store right neighbor
                            right_neighbor = (right_neighbor_id, neighbor_ip_address, neighbor_port)
                            logger.info(
                                f"ℹ️ Right neighbor: ID={right_neighbor_id}, IP={neighbor_ip_address}, Port={neighbor_port}")

                            # Set up the ring
                            assign_id()
                        else:
                            logger.error(f"⚠️ Invalid neighbor info: {receivedMessage}")
                elif "query_dht" in message:
                    # search process will list the order of the nodes that were visited

                    receivedMessage = clientSocket.recv(2048).decode()
                    logger.info(f"📩 Received from manager: {receivedMessage}")
                    print(receivedMessage)
                    search_process = []
                    nonvisit_ids = []
                    for i in range(ring_size):
                        nonvisit_ids.append(i)
                    fields = receivedMessage.split(" ")
                    if "SUCCESS" in receivedMessage:
                        print("Successful initialization of query request")
                        response_p_port = fields[2]
                        response_ip_addr = fields[1]
                        queried_event_id = input("Type in the event_id you wish to search for: ")
                        start_search_process(response_ip_addr, int(response_p_port), int(queried_event_id), nonvisit_ids
                                             , search_process)

                    else:
                        print("Error")
                elif "teardown" in message:
                    receivedMessage = clientSocket.recv(2048).decode()
                    print(receivedMessage)
                    if "SUCCESS" in receivedMessage:
                        print("Initiating teardown...")
                        teardown()
                else:
                    # Handle other commands
                    receivedMessage = clientSocket.recv(2048).decode()
                    logger.info(f"📩 Received from manager: {receivedMessage}")
                    print(receivedMessage)

            except Exception as e:
                logger.error(f"⚠️ Error processing command: {e}")

    except KeyboardInterrupt:
        logger.info("Peer terminated by user")

    finally:
        # Clean up
        if clientSocket:
            clientSocket.close()
        if peer_socket:
            peer_socket.close()
        logger.info("🤖 Peer shutdown complete")
        print("🤖 Now exiting the program...")


if __name__ == "__main__":
    main()
