import json
import asyncio
import logging
import discovery
import polling
import command
logging.getLogger("root").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARN)

lock = asyncio.Lock()

# Open and read the JSON file
with open('data/options.json', 'r') as file:
    data = json.load(file)

procdata = {
        "lock": lock, 
        "miners": [],
        "prefix": data["mqtt_prefix"],
        "server": data["mqtt_server"],
        "port": data["mqtt_port"],
        "user": data["mqtt_user"],
        "password": data["mqtt_password"],
        "subnet": data["miner_subnet"]
    }

async def main():
    await asyncio.gather(
        discovery.task(procdata),
        polling.task(procdata),
        command.task(procdata)
    )

asyncio.run(main())


