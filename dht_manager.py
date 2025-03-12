"""
Project Group 9 
Luan Nguyen, Somesh Harshavardhan Gopi Krishna, Sophia Gu, Kyongho Gong
Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi

dht_manager.py
"""

def main(): 
    import sys # System module for accessing CLI 
    
    # Checking if exactly 2 arguments are provided
    if len(sys.argv) !=2:
        print("Incorrect Command!")
        print("Usage: python3 dht_manager.py <port>")
        sys.exit(1)
        
    port = int(sys.argv[1])
    print(f"Testing port: {port}")
    
if __name__ == "__main__":
    main()