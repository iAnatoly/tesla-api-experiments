#!/usr/bin/env python3
import asyncio
import json
from datetime import datetime
from tesla_api import TeslaApiClient

class LocationManager:
    precision = 0.000005
    def __init__(self, locations):
        self.locations = locations

    def find_applicable_location(self, latitude, longitude):
        for location in self.locations:
            coords = location["coordinates"]
            lat = coords["latitude"]
            lon = coords["longitude"]

            if (abs(lat-latitude) < self.precision and abs(lon-longitude) < self.precision):
                return location 
        return None

class ScheduleManager:

    def __init__(self, location):
        self.location = location

    def _is_applicable(self, timeslot, now):
        (start_hour, start_min) = [ int(s) for s in timeslot["start"].split(':') ]
        (end_hour, end_min) = [ int (s) for s in timeslot["end"].split(':') ]
        start_time = now.replace(hour=start_hour, minute=start_min)
        end_time = now.replace(hour=end_hour, minute=end_min)

        return start_time<now and end_time>now

    def find_applicable_schedule(self):
        now = datetime.now()
        
        if self.location is None:
            return None

        for timeslot in self.location["schedule"]:
            if self._is_applicable(timeslot, now):
                return timeslot

        return None
    

async def main():
    with open('tesla-monitoring.conf.json') as conf_file:
        config = json.load(conf_file)

    print(json.dumps(config, indent=4))
    client = TeslaApiClient(token=config["token"])
    location_mgr = LocationManager(config["locations"])

    vehicles = await client.list_vehicles()
    vehicle = [ vehicle for vehicle in vehicles if vehicle.display_name == config["vehicle_name"] ][0]
    assert vehicle is not None

    drive_state = await vehicle.get_drive_state()
    print(json.dumps(drive_state, indent=4))
    
    location = location_mgr.find_applicable_location(drive_state["latitude"], drive_state["longitude"])
    if location is None:
        print("Cannot find applicable locations")

    sch_mgr = ScheduleManager(location)
    schedule = sch_mgr.find_applicable_schedule()
    if schedule is None:
        print("Cannot find applicable schedule")


    print(vehicle.state)

    await client.close()

if __name__=='__main__':
    asyncio.run(main())

