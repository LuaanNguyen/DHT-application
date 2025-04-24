# CSE434 Socket Programming Project: DHT Application

**Submit the project in a zip file named `Group<group_number>.zip**

**No late submission is accepted**

📆 Full project due: `05/02/2025`

## Project Overview 🌟

This project implements a Distributed Hash Table (DHT) system for storing and querying weather event data from NOAA's storm events database. The system consists of a central DHT Manager and multiple Peer nodes that form a ring topology for distributed data storage and retrieval.

## Filestone Submissions 📑

📌 Documentation: [Documentation](https://docs.google.com/document/d/1zdzy2W98iVG3k-rULQHCNX07EMCQG1knNZorXkv003U/edit?tab=t.0)  
📌 Design Doc: [CSE434: Socket Project](https://docs.google.com/document/d/1zIXYn8LTUxaovb8iLyP6x7aYPeaWQDtc4o6muHAUQH4/edit?tab=t.0#heading=h.mz71e5s6w1lg)  
📌 Time-space Diagram: [Time-space Diagram](https://docs.google.com/presentation/d/1ufCHWC4uRkZ89WrBdrQZOXyu7C4mGx7TVxSi8UaxVyE/edit#slide=id.p)  
📌 Video Demo: [Video](https://youtu.be/R7nA6OKfetA)

## Final Submissions 📑

📌 Design Doc:[CSE434: Socket Project Full](https://docs.google.com/document/d/1zIXYn8LTUxaovb8iLyP6x7aYPeaWQDtc4o6muHAUQH4/edit?tab=t.0)

## Architecture ⚙️

- Written in `Python`
- Communication via UDP sockets
- Ring-based DHT topology
- Data distribution using consistent hashing
- Version Control: `git` + `github`
- Dependencies: check `requirements.txt`

![Architecture](architecture.png)

### System Components

1. **DHT Manager**: Central coordinator responsible for peer registration, DHT setup, and managing peer state.
2. **Peers**: Distributed nodes that form the ring, store data, and route queries.
3. **Data Storage**: Each peer maintains a local hash table for storing weather event records.

💽 Storm Event Database: [NOAA's storm events database](https://www.ncdc.noaa.gov/stormevents/)

## Available Commands (To Be Updated) 🖥️

### DHT Manager Commands

The DHT Manager automatically processes commands received from peers.

### Peer Commands

Peers can issue the following commands to interact with the DHT:

2. [x] Code and documentation (25%). Submit your well-documented source code implementing the milestone of
       your DHT application.

   - Registers a peer with the manager
   - Example: `register peer1 127.0.0.1 8001 8002`

3. `setup-dht <peer-name> <n> <YYYY>`

- [x] For the end-hosts, consider using general{3|4|5}.asu.edu, the machines on the racks in BYENG 217, or
      installing your application on VMs on a LAN you configure in CloudLab, or using any other end-hosts available
      to you for the demo. (We use AWS EC2)

3. `dht-complete <peer-name>`

   - Signals that DHT setup is complete
   - Example: `dht-complete peer1`

4. `query-dht <peer-name>`

   - Initiates a query to find an event in the DHT
   - Example: `query-dht peer1`

5. `leave-dht <peer-name>`

   - Allows a peer to leave the DHT
   - Example: `leave-dht peer2`

## Reproduce Demo & Run the Program 🎯

This section provides step-by-step instructions to reproduce the DHT application demo as shown in the video. Follow these steps in order:

## Prerequisites

Make sure you have [Python](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installation/) installed on your local machine.

- Access to 4 distinct end-hosts (we use AWS EC2 instances)
- Python 3.x installed on all machines
- Git installed on all machines

## Step 1: Setup Environment

On each end-host:

```bash
# SSH into your EC2 Instance
ssh -i <your_pem_key> <your_EC2_public_IP>

# Clone the repository
git clone https://github.com/LuaanNguyen/DHT-application.git
cd DHT-application

# Setup Python environment
sudo apt install python3
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## a.b.c. Compile and Run Programs

1. Start the DHT Manager on one end-host:

```bash
python3 dht_manager.py 12345
```

2. On each of the 6 end-hosts, start a peer process:

```bash
python3 dht_peer.py 127.0.0.1 12345
```

## c. Register Peers

On each peer terminal, register with the manager:

```bash
# Terminal 1
register peer1 127.0.0.1 8001 8002

# Terminal 2
register peer2 127.0.0.1 8003 8004

# Terminal 3
register peer3 127.0.0.1 8005 8006

# Terminal 4
register peer4 127.0.0.1 8007 8008

# Terminal 5
register peer5 127.0.0.1 8009 8010

# Terminal 6
register peer6 127.0.0.1 8011 8012
```

## d. Setup DHT

Select one peer (e.g., peer1) to initiate DHT setup:

```bash
setup-dht peer1 5 1996
```

## e. Query DHT

On any peer terminal, issue queries with the following event IDs:

```bash
query-dht peer1
# When prompted, enter these event IDs one by one:
5536849
2402920
5539287
55770111
```

## f. Test Peer Leaving

1. Select one peer in the DHT to leave:

```bash
leave-dht peer2
```

2. Try querying from the peer that left:

```bash
query-dht peer2
# Enter any event ID (should fail as peer has left)
5536849
2402920
5539287
55770111
```

## g. Test Peer Joining

1. Select one of the remaining peers outside the DHT to join:

```bash
join-dht peer5
```

Might need to do peer restructuring (optional)

```bash
dht-rebuilt peer5 peer1
```

2. Issue a query from the remaining peer:

```bash
query-dht peer5

# Enter any event ID
5536849
2402920
5539287
55770111
```

## h. Teardown DHT

1. Have the leader issue teardown command:

```bash
teardown-dht peer1
```

2. Wait for all peers to process teardown:

```bash
teardown-complete peer1
```

## i. Graceful Termination

1. All peers should automatically de-register and exit
2. Manually terminate the manager process:

```bash
# On the manager's terminal
Ctrl+C
```

## Authors 👨‍💻👩‍💻

- Luan Nguyen
- Somesh Harshavardhan Gopi Krishna
- Sophia Gu
- Kyongho Gong

Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi
