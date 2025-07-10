import json
import time
import paho.mqtt.client as mqtt
import asyncio
from pyasic import get_miner
from pyasic.network import MinerNetwork
import logging
logging.getLogger("root").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARN)


# Open and read the JSON file
with open('data/options.json', 'r') as file:
    data = json.load(file)

async def scan_miners(subnet): 
    network = MinerNetwork.from_subnet(subnet)
    miners = await network.scan()
    return miners

miners = asyncio.run(scan_miners(data["miner_subnet"]))

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
    for miner in miners:
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

pf = data["mqtt_prefix"]

mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.username_pw_set(username=data["mqtt_user"], password=data["mqtt_password"])

logging.info("[MQTT] connecting")
mqttc.connect(data["mqtt_server"], data["mqtt_port"], 60)

async def loop_func(miner):
    mac = await miner.get_mac()
    uuid = "miner_" + mac.replace(":","")
    logging.info("[{}] loop started".format(miner))
    while 1:
        hashrate = await miner.get_hashrate()
        if not hashrate == None:
            mqttc.publish(pf + uuid + "/hashrate","{:.3f}".format(hashrate.rate))
        wattage = await miner.get_wattage()
        if not wattage == None:
            mqttc.publish(pf + uuid + "/wattage","{:.3f}".format(wattage))
        is_mining = await miner.is_mining()
        mqttc.publish(pf + uuid + "/is_mining","{}".format(is_mining))
        await asyncio.sleep(2.0)

async def publish_discovery(miner):
    mac = await miner.get_mac()
    mfr = miner.make
    model = await miner.get_model()
    uuid = "miner_" + mac.replace(":","")
    logging.info("[{}] publishing HA discovery".format(miner))

    common_dict = {
        "device": {
            "identifiers": ["miner_{}".format(uuid)],
            "name": "Miner {}".format(mac),
            "manufacturer": mfr,
            "model": model

        },
        "origin": {
            "name": "Miner2MQTT"
        },
        "qos": 1
    }

    enable_dict = {
        "name": "Mining Enable",
        "unique_id": uuid + "_enable",
        "state_topic": pf + uuid + "/is_mining",
        "state_on": True,
        "state_off": False,
        "command_topic": pf + uuid + "/command",
        "payload_on": "resume",
        "payload_off": "stop", 
    }

    hashrate_dict = {
        "name": "Hash Rate",
        "unique_id": uuid + "_hashrate",
        "state_topic": pf + uuid + "/hashrate",
        "unit_of_measurement": "TH/s",
    }

    wattage_dict = {
        "name": "Wattage",
        "unique_id": uuid + "_wattage",
        "state_topic": pf + uuid + "/wattage",
        "unit_of_measurement": "W",
    }

    mqttc.publish("homeassistant/switch/{}/config".format(uuid + "_enable"),"{}".format(json.dumps(common_dict | enable_dict)),qos=1,retain=True)
    mqttc.publish("homeassistant/sensor/{}/config".format(uuid + "_hashrate"),"{}".format(json.dumps(common_dict | hashrate_dict)),qos=1,retain=True)
    mqttc.publish("homeassistant/sensor/{}/config".format(uuid + "_wattage"),"{}".format(json.dumps(common_dict | wattage_dict)),qos=1,retain=True)

mqttc.loop_start()
asyncio.run(publish_discovery(miners[0]))
asyncio.run(loop_func(miners[0]))
mqttc.loop_stop()

