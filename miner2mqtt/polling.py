import asyncio
import aiomqtt
import logging
from discovery import miners

async def task(procdata):
    while 1:
        try:
            async with aiomqtt.Client(
                                    hostname = procdata["server"],
                                    port = procdata["port"],
                                    username = procdata["user"],
                                    password = procdata["password"],
                                    ) as client:  
                while 1:
                    logging.info("Polling")
                    async with procdata["lock"]:
                        for miner in procdata["miners"]:
                            mac = await miner.get_mac()
                            uuid = "miner_" + mac.replace(":","")
                            pf = procdata["prefix"]
                            hashrate = await miner.get_hashrate()
                            if not hashrate == None:
                                client.publish(pf + uuid + "/hashrate",payload="{:.3f}".format(hashrate.rate))
                            wattage = await miner.get_wattage()
                            if not wattage == None:
                                client.publish(pf + uuid + "/wattage",payload="{:.3f}".format(wattage))
                            is_mining = await miner.is_mining()
                            client.publish(pf + uuid + "/is_mining",payload="{}".format(is_mining))
                    await asyncio.sleep(2)
        except aiomqtt.MqttError:
            logging.ERROR(f"Connection lost; Reconnecting in 3 seconds ...")
            await asyncio.sleep(3)
