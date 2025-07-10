import asyncio
import logging
from discovery import miners

async def task(procdata):
    while 1:
        logging.info("Polling")
        async with procdata["lock"]:
            mqttc = procdata["mqtt"]
            for miner in procdata["miners"]:
                mac = await miner.get_mac()
                uuid = "miner_" + mac.replace(":","")
                pf = procdata["prefix"]
                hashrate = await miner.get_hashrate()
                if not hashrate == None:
                    mqttc.publish(pf + uuid + "/hashrate","{:.3f}".format(hashrate.rate))
                wattage = await miner.get_wattage()
                if not wattage == None:
                    mqttc.publish(pf + uuid + "/wattage","{:.3f}".format(wattage))
                is_mining = await miner.is_mining()
                mqttc.publish(pf + uuid + "/is_mining","{}".format(is_mining))
        await asyncio.sleep(2)