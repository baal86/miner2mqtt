import json
import paho.mqtt.client as mqtt
import asyncio
from pyasic import get_miner
from pyasic.network import MinerNetwork
import logging
import discovery
import polling
logging.getLogger("root").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARN)

lock = asyncio.Lock()

# Open and read the JSON file
with open('data/options.json', 'r') as file:
    data = json.load(file)

procdata = {
        "lock": lock, 
        "miners": [],
        "mqtt": None,
        "prefix": data["mqtt_prefix"]
    }

async def stop_mining(miner):
    logging.info("[{}] stop mining".format(miner))
    await miner.stop_mining()

async def resume_mining(miner):
    logging.info("[{}] resume mining".format(miner))
    await miner.resume_mining()

def on_connect(client, userdata, flags, rc):
    logging.info("[MQTT] connected with result code {}".format(rc))
    client.subscribe("miners/+/command")

async def find_miner_by_mac(mac):
    async with procdata["lock"]:
        for miner in procdata["miners"]:
            lmac = await miner.get_mac()
            lmac = lmac.replace(":","")
            if mac == lmac:
                return miner
        return None

def on_message(client, userdata, msg):
    tok = msg.topic.split("/")
    name = [t for t in tok if "miner_" in t][0]
    mac = name.split("_")[1]
    miner = asyncio.run(find_miner_by_mac(mac))
    if msg.payload == b'stop':
        asyncio.run(stop_mining(miner))
    if msg.payload == b'resume':
        asyncio.run(resume_mining(miner))

mqttc = mqtt.Client()
procdata["mqtt"] = mqttc
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.username_pw_set(username=data["mqtt_user"], password=data["mqtt_password"])
mqttc.connect(data["mqtt_server"], data["mqtt_port"], 60)
logging.info("[MQTT] connecting")

async def main():
    mqttc.loop_start()
    await asyncio.gather(
        discovery.task(procdata,data["miner_subnet"]),
        polling.task(procdata)
        )
    mqttc.loop_stop()

asyncio.run(main())


