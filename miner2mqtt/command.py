import aiomqtt
import logging
import asyncio

async def stop_mining(procdata,miner):
    logging.info("[{}] stop mining".format(miner))
    async with procdata["lock"]:
        await miner.stop_mining()

async def resume_mining(procdata,miner):
    logging.info("[{}] resume mining".format(miner))
    async with procdata["lock"]:
        await miner.resume_mining()

async def find_miner_by_mac(procdata,mac):
    async with procdata["lock"]:
        for miner in procdata["miners"]:
            lmac = await miner.get_mac()
            lmac = lmac.replace(":","")
            if mac == lmac:
                return miner
        return None


async def task(procdata):
    while 1:
        try:
            async with aiomqtt.Client(
                                    hostname = procdata["server"],
                                    port = procdata["port"],
                                    username = procdata["user"],
                                    password = procdata["password"],
                                    ) as client:  
                await client.subscribe(procdata["prefix"] + "+/command")
                async for message in client.messages:
                    tok = str(message.topic).split("/")
                    name = [t for t in tok if "miner_" in t][0]
                    mac = name.split("_")[1]
                    miner = await find_miner_by_mac(procdata,mac)
                    if message.payload == b'stop':
                        await stop_mining(procdata,miner)
                    if message.payload == b'resume':
                        await resume_mining(procdata,miner)
        except aiomqtt.MqttError:
            logging.ERROR(f"Connection lost; Reconnecting in 3 seconds ...")
            await asyncio.sleep(3)



