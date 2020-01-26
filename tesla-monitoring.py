#!/usr/bin/env python3
import asyncio
import json
from tesla_api import TeslaApiClient

async def main():
    with open('tesla-monitoring.conf.json') as conf_file:
        config = json.load(conf_file)

    print(json.dumps(config, indent=4))
    client = TeslaApiClient(token=config["token"])

    vehicles = await client.list_vehicles()
    for vehicle in vehicles:
        print(vehicle.display_name, vehicle.state, vehicle.id)
    await client.close()

if __name__=='__main__':
    asyncio.run(main())

