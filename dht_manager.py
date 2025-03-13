"""
Project Group 9
Luan Nguyen, Somesh Harshavardhan Gopi Krishna, Sophia Gu, Kyongho Gong
Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi

dht_manager.py
"""

from socket import*
import threading
from enum import Enum

class clientState(Enum):
    FREE = 1
    LEADER = 2
    INDHT = 3

def register_client(client_message):
    # See if 4 arguments total in register command (register +  4 args)
    command = client_message.split(" ")
    if len(command) != 5:
        print("FAILURE")

    # This is all for checking if the register command lines up with the syntax provided
    # The m-port, p-port, and IP address still need to be checked, though

    # This is to check if first argument is register
    if command[0] != "register":
        print("FAILURE")

    # Then, this is to check that the first command is not greater than 15 in length, not lesser than 1
    # also, to check if it's all alphabetical characters, and if the name isn't in the dictionary
    if len(command[1]) > 15 or len(command[1]) < 1:
        print("FAILURE")
    if not command[1].isalpha():
        print("FAILURE")
    if command[1] in client_dictionary:
        print("FAILURE")

    # the m-port has to be unique from a p-port, and it has to be unique for each process
    if command[3] == command[4]:
        print("FAILURE")
    if command[3] in client_dictionary.values():
        print("FAILURE")
    if command[4] in client_dictionary.values():
        print("FAILURE")
    
    # after error checking, I can add the registered client in the dictionary
    client_dictionary[command[1]] = {command[2], command[3], command[4]}
def handle_multiple_clients(connection, address):
    try:
        while True:
            # Receive the message that the client sent, and timestamp it
            clientMessage = connection.recv(2048).decode()

            # if the clientMessage is empty, step out of the while loop
            if not clientMessage:
                break
            elif "register" in clientMessage:
                connection.send(clientMessage.encode())
    # After the client has terminated with an exit, the server logs the exit, and closes the connection
    except ConnectionResetError:
        # add in the address of the client that terminated
        print("The client with address entered exit. Terminating connection for that client...")
        connection.close()

# the list of threads will maintain a client-server connection for each client
thread_list = []

# I'll set the hostname to my local machine, and the server port to 53333
hostname = '127.0.0.1'
serverPort = int(input("Please enter a port number between 1024 and 65535 "))

# I will create a UDP socket and bind the IP address and port address together
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind((hostname, serverPort))

client_dictionary = {}

# The server's terminal will print that it is now listening for up to 10 clients
print("The server is listening on port ", serverPort)
serverSocket.listen(10)

try:
    while True:
        # Accept any connections, and send over the server's welcome message to the client
        message, clientAddress = serverSocket.accept()
        welcomeMessage = "Welcome, client!\n"
        message.send(welcomeMessage.encode())

        # Then, start a new thread to handle the new client
        t = threading.Thread(target=handle_multiple_clients, args=(message, clientAddress))
        t.start()
        thread_list.append(t)

except KeyboardInterrupt:
    print("The process has been terminated")

serverSocket.close()
