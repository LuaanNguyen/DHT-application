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

# ============== SETTING LOG CONFIGS =============== #
logging.basicConfig(
    level=logging.INFO,
    format='► %(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # Log to file dht_peer.log + added 'utf-8' for fixing window error
        logging.FileHandler('dht_peer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============== GLOBAL VARIABLES =============== #
id = -1
right_neighbor = None
ring_size = -1
socket_array = []
input_file = ""

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
                
                response = f"{i} {ring_size} {peer_neighbor_ip_address} {peer_neighbor_port}"
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
    
    # Signal completion to manager
    dht_complete_message = f"✅ dht-complete {peer_name}"
    logger.info(f"📩 Sending dht-complete to manager: {dht_complete_message}")
    clientSocket.send(dht_complete_message.encode())
    completion_response = clientSocket.recv(2048).decode()
    logger.info(f"✅ DHT completion response: {completion_response}")
    
    return "SUCCESS" in completion_response

# ============== MAIN =============== #
def main():
    global clientSocket, peer_socket, id, ring_size, right_neighbor, input_file, peer_name
    
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
    peer_name = ""

    # Instructions
    print("✨ ---------------- Available commands ----------------- ✨")
    print("  ✅ register 〈peer-name〉 〈IPv4-address〉 〈m-port〉 〈p-port〉")
    print("  ✅ setup-dht 〈peer-name〉 〈n〉 〈YYYY〉")
    print("  ✅ dht-complete 〈peer-name〉")
    print("  ✅ exit")
    print("✨ ----------------------------------------------------- ✨")

    try:
        while True:
            # if the peer socket has been initialized, we can check if it's received a message
            if peer_socket is not None and check_udp_data(peer_socket):
                try:
                    data, addr = peer_socket.recvfrom(1024)
                    data_str = data.decode()
                    logger.info(f"Received data from {addr}: {data_str}")
                    
                    # Process peer message
                    mult_response = data_str.split(" ")
                    if len(mult_response) >= 4:
                        id = int(mult_response[0])
                        ring_size = int(mult_response[1])
                        right_neighbor_id = (id + 1) % ring_size
                        right_neighbor = (right_neighbor_id, mult_response[2], int(mult_response[3]))
                        logger.info(f"Set peer ID to {id}, ring size to {ring_size}")
                        logger.info(f"Right neighbor: ID={right_neighbor_id}, IP={mult_response[2]}, Port={mult_response[3]}")
                except Exception as e:
                    logger.error(f"⚠️ Error processing peer message: {e}")

            # query the client to send in an input message and send it
            message = input("Type in a message (type exit to terminate the connection): ")
            
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
                if "register" in message:
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
                            logger.info(f"ℹ️ Right neighbor: ID={right_neighbor_id}, IP={neighbor_ip_address}, Port={neighbor_port}")
                            
                            # Set up the ring
                            assign_id()
                        else:
                            logger.error(f"⚠️ Invalid neighbor info: {receivedMessage}")
                
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
    
