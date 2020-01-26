#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
from tesla_api import TeslaApiClient

class ScheduleManager:
    def __init__(self, locations):
        self.locations = locations

    def _is_applicable(self, timeslot, now):
        (start_hour, start_min) = [ int(s) for s in timeslot["start"].split(':') ]
        (end_hour, end_min) = [ int (s) for s in timeslot["end"].split(':') ]
        start_time = now.replace(hour=start_hour, minute=start_min)
        end_time = now.replace(hour=end_hour, minute=end_min)

        return start_time<now and end_time>now

    def find_applicable_schedule(self):
        now = datetime.now()
        
        for location in self.locations:
            for timeslot in location["schedule"]:
                if self._is_applicable(timeslot, now):
                    yield timeslot, location["coordinates"]

        return None
    
def find_applicable_location(pairs, latitude, longitude):
    precision = 0.000005
    for pair in pairs:
        coords = pair[1]
        lat = coords["latitude"]
        lon = coords["longitude"]

        if (abs(lat-latitude) < precision and abs(lon-longitude) < precision):
            yield pair[0]
    

async def main():
    with open('tesla-monitoring.conf.json') as conf_file:
        config = json.load(conf_file)

    print(json.dumps(config, indent=4))
    client = TeslaApiClient(token=config["token"])

    vehicles = await client.list_vehicles()
    vehicle = [ vehicle for vehicle in vehicles if vehicle.display_name == config["vehicle_name"] ][0]
    assert vehicle is not None


    sch_mgr = ScheduleManager(config["locations"])
    schedule_pairs = list(sch_mgr.find_applicable_schedule())
    if schedule_pairs is None:
        print("Cannot find applicable schedule")

    # if vehicle is offline, check if any of the schedules allow waking up. Wake up or quit
    if vehicle.state != 'online':
        if any(schedule[0]["wake_up"] for schedule in schedule_pairs):
            print("One or more schedules allow vehicle to be woken up")
            await vehicle.wake_up()
            while True:
                try:
                    await vehicle.get_drive_state()
                    break
                except:
                    pass

        else:
            print("Vehicle is offline, and none ogf the schedules allow wake up")
            return
    
    drive_state = await vehicle.get_drive_state()
    # print(json.dumps(drive_state, indent=4))

    schedules = find_applicable_location(schedule_pairs, drive_state["latitude"], drive_state["longitude"])
    if schedules is None:
        print("Cannot find a schedule with applicable locations")


    charge_state = await vehicle.charge.get_state()
    print(json.dumps(charge_state, indent=4))

    for schedule in schedules:
        print(schedule)
        if charge_state['charging_state'] in schedule['valid_states']:
            print('state is ok: ',charge_state['charging_state'],' in ',schedule['valid_states'])
        else:
            print('invalid state: ',charge_state['charging_state'])

    await client.close()

if __name__=='__main__':
    asyncio.run(main())

