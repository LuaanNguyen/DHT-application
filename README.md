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

## Environment Setup 💻

Make sure you have [Python](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installation/) installed on your local machine.

```bash
cd dht-application
python -m venv venv # create virtual environment
source venv/bin/activate # mac/linux
venv\Scripts\activate # windows
pip install -r requirements.txt # install dependencies
pip list # check if all dependencies are properly installed
```

## Run the program 🏋️‍♀️

### DHT Manager (`dht_manager.py`)

```bash
# python3 dht_manager.py <port>
python3 dht_manager.py 12345
```

### Peers (`dht_peer.py`)

```bash
# python3 dht_peer.py <manager_ip> <manager_port>
python3 dht_peer.py localhost 12345
```

## Available Commands 🖥️

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

## Reproduce Milestone 🎯

6. `leave-dht <peer-name>`

   - Allows a peer to leave the DHT
   - Example: `leave-dht peer2`

In your local computer, run:

```
python3 dht_manager.py 12345
```

or

For milestone, connect to your EC2 instance since we need to run the program on 2 distinct end hosts:

```
ssh -i <your_pem_key> <your_EC2_public_IP> # SSH into your EC2 Instance
git clone https://github.com/LuaanNguyen/DHT-application.git
cd DHT-application

If your EC2 distro is debian, you can run these commands to install neccessary depedencies:

```

# Install dependencies

> > > > > > > sudo apt install python3
> > > > > > > python3 -m venv venv
> > > > > > > source venv/bin/activate # For Linux/Debian
> > > > > > > pip install -r requirements.txt
> > > > > > > python3 dht_manager.py 12345

```

### 2. Initialize Multiple Peer Programs

In your local computer, on 3 different terminal windows, run reach peer with the same port as manager (`12345` in this case):

```

# python3 dht_peer localhost 12345

````
In separate terminal windows, start three peer instances:

```bash
python3 dht_peer.py localhost 12345
````

### 3. Register Each Peer

In each peer terminal, register with unique identifiers:

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

### 4. Set Up the DHT

From the terminal of the peer you want to designate as leader:

```bash
# In Terminal 1 (peer1)
setup-dht peer1 3 1999
setup-dht peer1 5 1996 # for video demo

```

The leader will:

1. Coordinate ring formation
2. Assign IDs to all peers
3. Read data from the specified year's CSV file
4. Distribute records across the DHT

### 5. Query the DHT

After setup completes:

```bash
# In any peer terminal
query-dht peer1

# When prompted for an event ID
40001
```

The system will:

1. Determine which peer should have the record
2. Route the query to that peer
3. Return the record if found

### 6. Testing Dynamic Membership (Optional)

To test a peer leaving the DHT:

```bash
# In Terminal 2 (peer2)
leave-dht peer2

# In Terminal 1 (peer1) to confirm ring restructuring
dht-rebuilt peer2 peer1
```

To test a peer joining the DHT:

```bash
# In a new Terminal 4
python3 dht_peer.py localhost 12345
register peer4 127.0.0.1 8007 8008
join-dht peer4

# In Terminal 1 (peer1) to confirm ring restructuring
dht-rebuilt peer4 peer1
```

### 7. Teardown the DHT

To properly shut down the DHT:

```bash
# In the leader's terminal (Terminal 1)
teardown-dht peer1

# After all peers have processed the teardown
teardown-complete peer1
```

## Troubleshooting 🔧

### Common Issues

1. **Connection Failures**

   - Ensure the manager is running before starting peers
   - Check that ports are available and not blocked by firewall

2. **Registration Failures**

   - Verify that peer names are unique
   - Ensure ports are not already in use

3. **DHT Setup Issues**

   - Confirm all peers are properly registered
   - Check that CSV data files exist in the project directory

4. **Query Problems**
   - Ensure the DHT is fully set up before querying
   - Verify that the event ID exists in the data set

## Project Structure 📁

- `dht_manager.py` - Central coordinator implementation
- `dht_peer.py` - Peer node implementation
- `validation_utils.py` - Command validation utilities
- `details-YYYY.csv` - Storm event data files for various years
- `requirements.txt` - Project dependencies

## Data Format 📊

The storm event data is stored in CSV files with the following fields:

- `event_id` - Unique identifier for the storm event
- `state` - US state where the event occurred
- `year`, `month`, `day` - Date of the event
- `event_type` - Type of storm (e.g., tornado, flood)
- `injuries`, `fatalities` - Impact of the event
- `damage_property` - Estimated property damage

## Authors 👨‍💻👩‍💻

- Luan Nguyen
- Somesh Harshavardhan Gopi Krishna
- Sophia Gu
- Kyongho Gong

Arizona State University
CSE434: Computer Networks
Prof. Bharatesh Chakravarthi
