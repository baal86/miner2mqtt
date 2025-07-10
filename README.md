# Miner 2 MQTT
## Purpose
This home assistant addon integrates Bitcoin miners controllable by `pyasic` like the Antminer into Homeasssistant via MQTT.

## Installation
Add the repository `https://github.com/baal86/miner2mqtt` to your addon store repositories and install the addon.

## Configuration
The following configuration items are required:

- MQTT server URL
- MQTT server port
- MQTT server username
- MQTT server password
- MQTT prefix for miners, e.g. `miners/`
- Subnet to scan for miners

The addon will post discovery topics for homeassistant configuration.

## Known Issues
**This is in early development** There are known issues!

- I only have one miner so concurrent operation will likely remain untested for a while.
- Currently only the following features of the miner are implemented. It is planned to implement all features of the base miner class of `pyasic` in the very near future.
  - Enable switch with status feedback
  - Wattage sensor
  - Hashrate sensor
 
Contributions are welcome but please be patient. I am an electrical engineer doing this in my free time and not a professional coder.
