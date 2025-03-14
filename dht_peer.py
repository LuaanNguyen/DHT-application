"""
Project Group 9
Luan Nguyen, Somesh Harshavardhan Gopi Krishna, Sophia Gu, Kyongho Gong
Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi

dht_peer.py
"""

from socket import*
import sys
import logging  

# ============== SETTING LOG CONFIGS =============== #
logging.basicConfig(
    level=logging.INFO,
     format='%(asctime)s - %(levelname)s - %(message)s',  # Set log message format
    handlers=[
        logging.FileHandler('dht_peer.log'),  # Log to file dht_peer.log
        logging.StreamHandler()  # Log to console
    ]
)

logger = logging.getLogger(__name__)

# ============== MAIN =============== #
def main():    
    if len(sys.argv) != 3:
        logger.error("Incorrect number of command line arguments")
        print("Usage: python3 dht_peer.py <manager_ip> <manager_port>")
        sys.exit(1)

    # define the server name and port for the client to connect to
    serverName = sys.argv[1]
    try:
        serverPort = int(sys.argv[2])
        if serverPort <= 1024 or serverPort > 65535:
            logger.error(f"Port number out of range: {serverPort}. Please specify a port address within appropriate bounds (1024 - 65535)")
            sys.exit(1)
    except ValueError:
        logger.error("Invalid port number format")
        sys.exit(1)

     # create a UDP client socket
    try:
        clientSocket = socket(AF_INET, SOCK_DGRAM)
        clientSocket.connect((serverName, serverPort))
        logger.info(f"Connected to manager at {serverName}:{serverPort}")
    except Exception as e:
        logger.error(f"Failed to connect to manager: {str(e)}")
        sys.exit(1)

    try: 
        while True:
            # query the client to send in an input message and send it
            message = input("Type in a message (type exit to terminate the connection):")
          

            # if the message is exit, exit the loop
            if message == "exit":
                logger.info("User requested exit")
                break
            
            try:
                clientSocket.send(message.encode())
                logger.info(f"Sent message to manager: {message}")
                # receive response from manager
                receivedMessage = clientSocket.recv(2048).decode()
                logger.info(f"Received response from manager: {receivedMessage}")
            except Exception as e:
                logger.error(f"Communication error: {str(e)}")
                print("Error communicating with manager")
                
    except KeyboardInterrupt:
        logger.info("Peer terminated by user")
        print(f"The client terminated")
        
    clientSocket.close()
    logger.info("Connection closed")


if __name__ == "__main__":
    main()
    
    
