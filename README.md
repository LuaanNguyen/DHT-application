# CSE434 Socket Programming Project: DHT Application

**Submit the project in a zip file named `Group<group_number>.zip**

**No late submission is accepted**

📆 Full project due: `05/02/2025`

## Filestone Submissions 📑

📌 Documentation: [Documentation](https://docs.google.com/document/d/1zdzy2W98iVG3k-rULQHCNX07EMCQG1knNZorXkv003U/edit?tab=t.0)  
📌 Design Doc: [CSE434: Socket Project](https://docs.google.com/document/d/1zIXYn8LTUxaovb8iLyP6x7aYPeaWQDtc4o6muHAUQH4/edit?tab=t.0#heading=h.mz71e5s6w1lg)  
📌 Time-space Diagram: [Time-space Diagram](https://docs.google.com/presentation/d/1ufCHWC4uRkZ89WrBdrQZOXyu7C4mGx7TVxSi8UaxVyE/edit#slide=id.p)  
📌 Video Demo: [Video](https://youtu.be/R7nA6OKfetA)

## Final Submissions 📑

📌 Documentation:
📌 Design Doc:[CSE434: Socket Project Full](https://docs.google.com/document/d/1zIXYn8LTUxaovb8iLyP6x7aYPeaWQDtc4o6muHAUQH4/edit?tab=t.0)
📌 Time-space Diagram:
📌 Video Demo:

## Architecture ⚙️

- Written in `Python`
- Version Control: `git` + `github`
- Dependecies: check `requirements.txt`

![Architecture](architecture.png)

💽 Storm Event Database: [NOAA's storm events database](https://www.ncdc.noaa.gov/stormevents/)

## Environment Setup 💻

Make sure you have [Python](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installation/) installed on your local machine.

```
cd dht-application
python -m venv venv # create virtual enviroment
source venv/bin/activate # mac
venv\Scripts\activate # window
pip install -r requirements.txt # install dependecies
pip list # check if all dependecies are properly installed
```

## Run the program 🏋️‍♀️

### DHT Manager (`dht_manager.py`)

```
# python3 dht_manager.py <port>
python3 dht_manager.py 12345
```

### Peers (`dht_peer.py`)

```
# python3 dht_peer.py <manager_ip> <manager_port>

python3 dht_peer.py localhost 12345

```

## Reproduce 🎯

This is step by step on reproducing the project requirements.

### Initialize DHT Manager Program

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
```

If your EC2 distro is debian, you can run these commands to install neccessary depedencies:

```
sudo apt install python3
python3 -m venv venv
source venv/bin/activate # For Linux/Debian
pip install -r requirements.txt
python3 dht_manager.py 12345
```

### Initialize Peer Program

In your local computer, on 3 different terminal windows, run reach peer with the same port as manager (`12345` in this case):

```
python3 dht_peer localhost 12345
```

### Register each peer

```
# terminal 1
register peer1 127.0.0.1 8001 8002

# terminal 2
register peer2 127.0.0.1 8003 8004

# terminal 3
register peer3 127.0.0.1 8005 8006
```

### Set up DHT

Peer1 sends `setup-dht` to the manager. The manager then proceeds to check and peer1 is now able to set up the ring by communicating with other peers.

```
# leader (terminal 1)
setup-dht peer1 3 1999
```

If everything works correctly, you'll see logs in the manager showing the DHT setup process and completion.

### After setup completes

```
# In any peer
query-dht peer1
# Then enter an event_id to search
40001
```

### DHT complete

```
# leader
dht-complete peer1
```

You should see a receipt ("SUCCESS") of a dht-complete indicates that the leader has completed all the steps required to set up the DHT.
