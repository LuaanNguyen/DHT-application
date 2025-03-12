"""
Project Group 9 
Luan Nguyen, Somesh Harshavardhan Gopi Krishna, Sophia Gu, Kyongho Gong
Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi

dht_peer.py
"""

def main():
    import sys 
    
    if len(sys.argv) != 3: 
        print("Incorrect Command!")
        print("Usage: python3 dht_peer.py <manager_ip> <manager_port>")
        sys.exit(1)
        
    manager_ip = sys.argv[1]
    manager_port = sys.argv[2]
    print(f"Manager ip: {manager_ip}")
    print(f"Testing port: {manager_port}")
    
    
if __name__ == "__main__":
    main()
    
    