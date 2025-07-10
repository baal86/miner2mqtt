import asyncio
from pyasic import get_miner
from pyasic.network import MinerNetwork
import logging
import json

miners = []

async def scan_miners(subnet): 
    network = MinerNetwork.from_subnet(subnet)
    miners = await network.scan()
    return miners
    
async def publish_discovery(mqttc,miner,prefix):
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
        "state_topic": prefix + uuid + "/is_mining",
        "state_on": True,
        "state_off": False,
        "command_topic": prefix + uuid + "/command",
        "payload_on": "resume",
        "payload_off": "stop", 
    }

    hashrate_dict = {
        "name": "Hash Rate",
        "unique_id": uuid + "_hashrate",
        "state_topic": prefix + uuid + "/hashrate",
        "unit_of_measurement": "TH/s",
    }

    wattage_dict = {
        "name": "Wattage",
        "unique_id": uuid + "_wattage",
        "state_topic": prefix + uuid + "/wattage",
        "unit_of_measurement": "W",
    }

    mqttc.publish("homeassistant/switch/{}/config".format(uuid + "_enable"),"{}".format(json.dumps(common_dict | enable_dict)),qos=1,retain=True)
    mqttc.publish("homeassistant/sensor/{}/config".format(uuid + "_hashrate"),"{}".format(json.dumps(common_dict | hashrate_dict)),qos=1,retain=True)
    mqttc.publish("homeassistant/sensor/{}/config".format(uuid + "_wattage"),"{}".format(json.dumps(common_dict | wattage_dict)),qos=1,retain=True)

async def task(procdata,subnet):
    while 1:
        logging.info("Discovering")
        async with procdata["lock"]:
            procdata["miners"] = await scan_miners(subnet)
            for miner in procdata["miners"]:
                await publish_discovery(procdata["mqtt"],miner,procdata["prefix"])
        await asyncio.sleep(30)
