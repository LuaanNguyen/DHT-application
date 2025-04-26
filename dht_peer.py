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
import csv
import random
import time

# ============== SETTING LOG CONFIGS =============== #
logging.basicConfig(
    level=logging.INFO,
    # ►  %(asctime)s - %(levelname)s - %(message)s
    format='►  %(message)s',
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
initialized = False  # New state flag
data_received = False  # Flag to track if data has been received
last_heartbeat_time = 0
heartbeat_interval = 10  # seconds

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
    logger.info(f"🔍 Starting search process for event {event_id}")
    
    # Calculate where this event should be
    find_pos = calculate_pos(event_id)
    find_id = calculate_id(find_pos)
    
    logger.info(f"Event {event_id} should be at position {find_pos} on node {find_id}")
    
    if find_id == id:
        # Check local DHT
        if 0 <= find_pos < len(DHT) and DHT[find_pos] is not None:
            search_record = DHT[find_pos]
            if int(search_record[0]) == event_id:
                print(f"\n✅ SUCCESSFULLY FOUND THE STORM WITH EVENT_ID: {event_id}")
                print(f"Record: {search_record}")
                return
        
        print(f"\n❌ Event {event_id} not found at node {id}")
    else:
        # Add current node to search path
        id_seq.append(id)
        if id in unvisited_ids:
            unvisited_ids.remove(id)
        
        # Check if right_neighbor is set before forwarding
        if right_neighbor is not None:
            # Forward to next node
            logger.info(f"Forwarding search to neighbor node {right_neighbor}")
            start_message = f"start-query {event_id}"
            try:
                peer_socket.sendto(start_message.encode(), (right_neighbor[1], int(right_neighbor[2])))
                print(f"Passing query for event {event_id} to next node")
            except Exception as e:
                logger.error(f"⚠️ Error forwarding search: {e}")
        else:
            # Handle case when right_neighbor isn't set
            logger.error("⚠️ Cannot forward search: right_neighbor not set")
            print(f"❌ Cannot continue search: ring not properly initialized")


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


def isprime(n):
    """Check if a number is prime."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

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
                        try:
                            # we can initialize the DHT now
                            global DHT, data_received
                            if DHT_size == -1:
                                DHT_size = int(mult_response[1])
                                logger.info(f"📊 Initializing DHT with size: {DHT_size}")
                                DHT = [None] * DHT_size
                            
                            curr_record = mult_response[2:16]
                            logger.info(f"📥 Received record: event_id={curr_record[0]}, state={curr_record[1]}")
                            forward_record(curr_record)
                            
                            # Mark that we've received data
                            data_received = True
                            
                            # Check initialization status after receiving data
                            check_initialization_status()
                        except Exception as e:
                            logger.error(f"⚠️ Error processing store message: {e}")
                    elif "reset-id" in data_str:
                        parts = data_str.split(" ")
                        if len(parts) >= 5:
                            old_id = int(parts[1])
                            ring_size = int(parts[2])
                            neighbor_ip = parts[3]
                            neighbor_port = int(parts[4])

                            # Update local state properly
                            id = old_id
                            right_neighbor = ((id + 1) % ring_size, neighbor_ip, neighbor_port)
                            print(f"✅ [ reset-id ]  New ID: {id}, New neighbor: {right_neighbor}")
                            
                            # Make sure DHT size is maintained if already set
                            if DHT_size > 0 and len(DHT) > 0:
                                # Recalculate which records should be stored locally
                                # This is a simplified approach - ideally you'd redistribute data
                                new_DHT = [None] * DHT_size
                                for pos, record in enumerate(DHT):
                                    if record is not None:
                                        event_id = int(record[0])
                                        new_pos = calculate_pos(event_id) 
                                        new_node = calculate_id(new_pos)
                                        if new_node == id:  # If this record should still be here
                                            new_DHT[new_pos] = record
                                DHT = new_DHT  # Update local DHT

                            # Continue propagating the reset-id message
                            if id != ring_size - 1:
                                next_id = (id + 1) % ring_size
                                next_msg = f"reset-id {next_id} {ring_size} {neighbor_ip} {neighbor_port}"
                                try:
                                    peer_socket.sendto(next_msg.encode(), (neighbor_ip, int(neighbor_port)))
                                    print(f"📩  Sent reset-id to neighbor {next_id}")
                                except Exception as e:
                                    logger.error(f"⚠️ Error forwarding reset-id: {e}")
                    elif "start-query" in data_str:

                        query_event_id = int(mult_response[1])
                        nonvisit_ids = []
                        search_process = []
                        for i in range(ring_size):
                            nonvisit_ids.append(i)

                        start_search_process(peer_socket.getpeername()[0], peer_socket.getpeername()[1], query_event_id, nonvisit_ids, search_process)
                    elif "heartbeat" in data_str:
                        parts = data_str.split(" ")
                        if len(parts) >= 3:
                            sender_id = int(parts[1])
                            sender_name = parts[2]
                            logger.info(f"💓 Received heartbeat from peer {sender_name} (ID: {sender_id})")
                            
                            # Send heartbeat response
                            try:
                                response = f"heartbeat-ack {id} {peer_name}"
                                peer_socket.sendto(response.encode(), addr)
                            except Exception as e:
                                logger.error(f"⚠️ Failed to send heartbeat response: {e}")
                    elif "heartbeat-ack" in data_str:
                        parts = data_str.split(" ")
                        if len(parts) >= 3:
                            responder_id = int(parts[1])
                            responder_name = parts[2]
                            logger.info(f"💓 Received heartbeat acknowledgment from peer {responder_name} (ID: {responder_id})")
                    elif "redistribute" in data_str:
                        parts = data_str.split(" ")
                        
                        if len(parts) >= 3:
                            action = parts[1]
                            affected_peer = parts[2]
                            logger.info(f"📊 Redistribution triggered: {action} {affected_peer}")
                        else:
                            logger.info(f"📊 General redistribution triggered")
                        
                        # Only the leader should handle redistribution
                        if id == 0:  # Leader
                            logger.info("📊 Leader initiating data redistribution")
                            
                            # Recalculate which records belong to which peers after topology change
                            redistribute_records()
                    else:
                        if len(mult_response) >= 4:
                            # global right_neighbor
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
                elif "query-dht" in message:
                    receivedMessage = clientSocket.recv(2048).decode()
                    logger.info(f"📩 Received from manager: {receivedMessage}")
                    print(receivedMessage)
                    
                    if "SUCCESS" in receivedMessage:
                        # Wait for initialization to complete
                        max_wait = 5  # Maximum wait time in seconds
                        wait_interval = 0.5  # Check every half second
                        
                        logger.info(f"⏳ Waiting for DHT initialization (max {max_wait}s)...")
                        
                        # Wait for initialization or timeout
                        start_time = time.time()
                        while not check_initialization_status() and (time.time() - start_time) < max_wait:
                            time.sleep(wait_interval)
                            logger.info("⏳ Still waiting for initialization...")
                        
                        # Check if we're ready after waiting
                        if not initialized:
                            logger.warning("⚠️ Query timeout: Peer not fully initialized")
                            print("⚠️ This peer is not properly initialized in the DHT.")
                            print("⚠️ Make sure all peers are registered and DHT is set up.")
                            print("⚠️ If this persists, try restarting the peer.")
                            continue
                        
                        # Peer is ready, proceed with query
                        logger.info("✅ Peer ready. Proceeding with query.")
                        
                        # Prompt for event ID
                        print("\n📝 Enter event ID to search for:")
                        event_id_input = input("Event ID > ")
                        try:
                            event_id = int(event_id_input)
                            logger.info(f"🔍 Searching for event_id: {event_id}")
                            
                            # Check if DHT is initialized
                            if DHT_size <= 0 or len(DHT) == 0:
                                logger.error("⚠️ DHT storage not initialized")
                                print("❌ Cannot search: DHT storage not initialized")
                                continue
                                
                            # Initialize search parameters
                            nonvisit_ids = list(range(ring_size))
                            search_process = []
                            
                            # Calculate where this event should be
                            find_pos = calculate_pos(event_id)
                            find_id = calculate_id(find_pos)
                            
                            logger.info(f"Event {event_id} should be at position {find_pos} on node {find_id}")
                            
                            if find_id == id:
                                # Check local DHT
                                if 0 <= find_pos < len(DHT) and DHT[find_pos] is not None:
                                    search_record = DHT[find_pos]
                                    if int(search_record[0]) == event_id:
                                        print(f"\n✅ SUCCESSFULLY FOUND THE STORM WITH EVENT_ID: {event_id}")
                                        print(f"Record: {search_record}")
                                    else:
                                        print(f"\n❌ Event {event_id} not found (position occupied by event {search_record[0]})")
                                else:
                                    print(f"\n❌ Event {event_id} not found in DHT")
                            else:
                                # Check if right_neighbor is set
                                if right_neighbor is None:
                                    logger.error("⚠️ Right neighbor not set, cannot forward search")
                                    print("❌ Cannot search: ring neighbors not set up correctly")
                                else:
                                    # Forward the search
                                    start_message = f"start-query {event_id}"
                                    try:
                                        logger.info(f"Forwarding search to node {right_neighbor}")
                                        peer_socket.sendto(start_message.encode(), (right_neighbor[1], int(right_neighbor[2])))
                                        print(f"Forwarding search for event {event_id} to next node")
                                    except Exception as e:
                                        logger.error(f"⚠️ Error forwarding search: {e}")
                        except ValueError:
                            logger.error(f"⚠️ Invalid event ID: {event_id_input}. Please enter a number.")
                        except Exception as e:
                            logger.error(f"⚠️ Error during search: {e}")
                    else:
                        logger.error("❌ Query failed. Make sure DHT is set up properly.")
                elif "leave-dht" in message:
                    leave_dht(message, clientSocket, receivedMessage)
                elif "dht-rebuilt" in message:
                    receivedMessage = clientSocket.recv(2048).decode()
                    print(receivedMessage)

                    if "SUCCESS" in receivedMessage:
                        print("✅  DHT rebuild...")

                        if id == 0:
                            assign_id()
                    else:
                        print("❌  DHT rebuild fail...")
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


def leave_dht(message, clientSocket, receivedMessage):
    global id, ring_size, DHT, DHT_size, input_file, right_neighbor
    
    if "SUCCESS" in receivedMessage:
        print("✅ Leave request accepted...")
        
        # After successfully leaving, reset local state
        old_id = id  # Save for reset-id message
        old_ring_size = ring_size
        old_right_neighbor = right_neighbor
        
        # Reset all local state variables
        id = -1
        ring_size = -1
        DHT = []
        DHT_size = -1
        input_file = ""
        
        # Then propagate reset-id with old values
        if old_right_neighbor is not None:
            reset_msg = f"reset-id {old_id} {old_ring_size} {old_right_neighbor[1]} {old_right_neighbor[2]}"
            peer_socket.sendto(reset_msg.encode(), (old_right_neighbor[1], old_right_neighbor[2]))
            print(f"📩 Sent reset-id to neighbor: {old_right_neighbor}")
        
        # Set right_neighbor to None last
        right_neighbor = None
    else:
        print("❌ leave-dht request denied...")


# Add new function to check initialization status
def check_initialization_status():
    """Check if the peer is fully initialized and update the initialized flag"""
    global initialized, data_received
    
    basic_setup = (id >= 0 and ring_size > 0 and right_neighbor is not None)
    dht_setup = (DHT_size > 0 and len(DHT) > 0)
    
    # Update initialization status
    initialized = basic_setup and dht_setup and data_received
    
    if initialized:
        logger.info("✅ Peer fully initialized and ready for queries")
    else:
        missing = []
        if id < 0: missing.append("ID not assigned")
        if ring_size <= 0: missing.append("ring size not set")
        if right_neighbor is None: missing.append("neighbor not assigned")
        if DHT_size <= 0 or len(DHT) <= 0: missing.append("DHT not initialized")
        if not data_received: missing.append("no data received")
        
        logger.info(f"⏳ Peer initialization incomplete. Missing: {', '.join(missing)}")
    
    return initialized


# Add heartbeat function
def send_heartbeat():
    """Send a heartbeat to the right neighbor to check if it's alive"""
    global right_neighbor, last_heartbeat_time
    
    current_time = time.time()
    
    # Only send heartbeat if we're initialized and it's time
    if initialized and right_neighbor is not None and (current_time - last_heartbeat_time) >= heartbeat_interval:
        try:
            heartbeat_msg = f"heartbeat {id} {peer_name}"
            peer_socket.sendto(heartbeat_msg.encode(), (right_neighbor[1], int(right_neighbor[2])))
            logger.info(f"💓 Sent heartbeat to neighbor {right_neighbor[0]}")
            last_heartbeat_time = current_time
        except Exception as e:
            logger.error(f"⚠️ Failed to send heartbeat: {e}")


# Add redistributeRecords function
def redistribute_records():
    """Redistribute data records after topology changes"""
    global input_file
    
    # Only the leader should do this
    if id != 0:
        logger.warning("⚠️ Only the leader can redistribute records")
        return
    
    logger.info(f"📊 Redistributing data from {input_file}")
    
    try:
        # Re-read data file
        with open(input_file, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader)  # Skip header
            
            # Process each record
            for row in csvreader:
                # Recalculate where this record should go
                forward_record(row)
                
        logger.info("✅ Data redistribution complete")
    except Exception as e:
        logger.error(f"⚠️ Error during data redistribution: {e}")


# Add at the top level before the main loop
def reconnect_to_manager():
    """Attempt to reconnect to the manager if connection is lost"""
    global clientSocket, serverName, serverPort
    
    try:
        logger.info(f"🔄 Attempting to reconnect to manager at {serverName}:{serverPort}")
        
        # Close old socket if it exists
        if clientSocket:
            try:
                clientSocket.close()
            except:
                pass
        
        # Create new socket
        clientSocket = socket(AF_INET, SOCK_DGRAM)
        clientSocket.connect((serverName, serverPort))
        
        logger.info("✅ Successfully reconnected to manager")
        return True
    except Exception as e:
        logger.error(f"⚠️ Failed to reconnect: {e}")
        return False


if __name__ == "__main__":
    main()
