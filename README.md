# CSE434 Socket Programming Project: DHT Application

📆 Available: `Sunday 02/26/2025`

📆 Midestone due: `Sunday 03/23/2025`

📆 Full project due: `04/04/2025`

📌 Link to Design Doc: [CSE434: Socket Project](https://docs.google.com/document/d/1zdzy2W98iVG3k-rULQHCNX07EMCQG1knNZorXkv003U/edit?tab=t.0)

## Architecture ⚙️

- Written in Python
- Version Control: git + github
- Main parts:
  - DHT Manager (always-on)
  - Peers (storage nodes)
  - Communication patterns (Hot Potato)
    - Manager-Peer communication
    - Peer-to-peer (P2P) communication

![Architecture](architecture.png)

## Setting up the python environment 💻

```
cd dht-application
python -m venv venv # create virtual enviroment
source venv/bin/activate # mac
venv\Scripts\activate # window
pip install -r requirements.txt # install dependecies
pip list # check if all dependecies are properly installed
```

## Run the program 🏋️‍♀️

### DHT Manager

```
# Usage: python3 dht_manager.py <port>
python3 dht_manager.py 12345

```

### Peers

(May have multiple instance running)

```
# Usage: python3 dht_peer.py <manager_ip> <manager_port>
python3 dht_peer.py localhost 12345

```

## Milestone Submission 📑

- Implement following commands to the DHT Manager
  - [ ] register
  - [ ] setup-dht
  - [ ] dht-complete
- File file must contain:
  - [ ] 50%: Design of the DHT application program (.pdf)
  - [ ] 25%: Code and documentation
  - [ ] 25%: Video Demo

**_Refer to the pdf for the detailed versions_**
