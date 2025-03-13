from socket import*
import sys

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

while True:
    # query the client to send in an input message and send it
    message = input("Type in a message (type exit to terminate the connection):")
    clientSocket.send(message.encode())

    # if the message is exit, exit the loop
    if message == "exit":
        break

    # otherwise, print the message that the server echoed back
    receivedMessage = clientSocket.recv(2048).decode()
    print(receivedMessage)

print("Now exiting the program...")
    
    
