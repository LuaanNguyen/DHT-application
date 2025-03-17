"""
Project Group 9
Luan Nguyen, Somesh Harshavardhan Gopi Krishna, Sophia Gu, Kyongho Gong
Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi

validation_utils.py - Utility functions for command validation
"""

import ipaddress
import logging

logger = logging.getLogger(__name__)

def check_register_command(client_message, client_dictionary):
    """
    Validate registration command format
    
    Args:
        client_message: The message to validate
        client_dictionary: Dictionary of registered clients
        
    Returns:
        bool: True if valid, False otherwise
    """
    # See if 4 arguments total in register command (register + 4 args)
    client_message_arr = client_message.split(" ")
    command =  client_message_arr[0]
    peer_name =  client_message_arr[1]
    ip_addr =  client_message_arr[2]
    m_port =  client_message_arr[3]
    p_port =  client_message_arr[4]
    
    if len(client_message_arr) != 5:
        logger.warning("Invalid number of arguments")
        return False

    # Check if first argument is register
    if command != "register":
        logger.warning("First argument is not 'register'")
        return False

    # Check peer name requirements
    if len(peer_name) > 15 or len(peer_name) < 1:
        logger.warning(f"Invalid peer name length: {peer_name}")
        return False
    if not peer_name.isalnum():
        logger.warning(f"Peer name not alphanumeric: {peer_name}")
        return False
    if peer_name in client_dictionary:
        logger.warning(f"Peer name already exists: {peer_name}")
        return False

    # Check IP address
    if not IP_address_valid(ip_addr):
        logger.warning(f"Invalid IP address: {ip_addr}")
        return False

    # Check ports
    if m_port == p_port:
        logger.warning(f"m_port and p_port are identical: {m_port}")
        return False

    return True

def IP_address_valid(entered_IP_address):
    """
    Validate IP address format
    
    Args:
        entered_IP_address: IP address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        ipaddress.ip_address(entered_IP_address)
        return True
    except ValueError:
        return False

def check_setupDHT(client_message, client_dictionary, DHT_set_up):
    """
    Validate setup-dht command format
    
    Args:
        client_message: The message to validate
        client_dictionary: Dictionary of registered clients
        DHT_set_up: Boolean indicating if DHT is already set up
        
    Returns:
        bool: True if valid, False otherwise
    """
    command = client_message.split(" ")

    # Check command name
    if command[0] != "setup-dht":
        logger.warning("First argument is not 'setup-dht'")
        return False

    # Check if peer exists
    if not command[1] in client_dictionary:
        logger.warning(f"Peer {command[1]} not registered")
        return False

    # Check n value
    try:
        user_num = int(command[2])
    except ValueError:
        logger.warning("Invalid number format for n")
        return False

    # Check n constraints
    if user_num < 3:
        logger.warning(f"n must be at least 3, got {user_num}")
        return False
    if user_num > len(client_dictionary):
        logger.warning(f"Not enough registered peers. Need {user_num}, have {len(client_dictionary)}")
        return False

    # Check year
    try:
        year = int(command[3])
    except ValueError:
        logger.warning("Invalid year format")
        return False

    # Check year range
    if year < 1950 or year > 2019:
        logger.warning(f"Year must be between 1950 and 2019, got {year}")
        return False

    # Check if DHT already exists
    if DHT_set_up:
        logger.warning("DHT already set up")
        return False

    return True 