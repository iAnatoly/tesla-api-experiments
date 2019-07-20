#!/usr/bin/env python3
from requests import post, get
from requests.exceptions import ConnectionError
from requests.utils import default_headers
from getpass import getpass
from time import sleep
from json import dumps, dump, load  # https://docs.python.org/2/library/json.html
from argparse import ArgumentParser # https://docs.python.org/3.3/library/argparse.html
from os.path import expanduser

# Tesla API reference:
# * https://tesla-api.timdorr.com/
# * https://www.teslaapi.io/vehicles/commands

class InvalidCredentialsException(Exception):
    pass

class VehicleAsleepException(Exception):
    pass

class UnexpectedResponseException (Exception):
    pass

class UnauthorizedException (Exception):
    pass

class Config:
    default_email = 'anatoly.ivanov@gmail.com'

    def __init__(self):
        parser = ArgumentParser(description='Send commands to tesla.')
        parser.add_argument('-l', '--set-charge-limit', dest='limit', type=int, default=0, help='Percentage of the battery to set the charge to')
        parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Verbose mode (priont json responses)')
        parser.add_argument('-r', '--revoke', dest='revoke', action='store_true', default=False, help='Revoke saved token (logout) and exit')
        parser.add_argument('-w', '--wakeuip', dest='wakeup', action='store_true', default=False, help='Wake up vehicle')
        parser.add_argument('-d', '--dump', dest='dump_json', action='store_true', default=False, help='Dump the full config into json')
        parser.add_argument('-c', '--charge', dest='cmd_charge', type=str, default='none', help='Start or stop charge', choices=['start','stop'])
        
        
        
        args = parser.parse_args()
        
        self.limit = args.limit
        self.debug = args.verbose
        self.revoke = args.revoke
        self.wakeup = args.wakeup
        self.dump = args.dump_json
        self.rate = 0.13 # let us use PGE EV rate as baseline
        self.charge_cmd = args.cmd_charge

    def get_credentials(self):
        self.login = input('Enter your tesla.com login: [default={}]: '.format(Config.default_email))
        if not self.login: 
            self.login = Config.default_email
        else:
            self.login = self.login.strip()

        self.password = getpass('Please eneter password for {}: '.format(self.login))

class TeslaBase:
    ## API config
    client_id="81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
    client_secret="c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3"
    root = 'https://owner-api.teslamotors.com/api/1/{}'    
    oauth_token = 'https://owner-api.teslamotors.com/oauth/token'
    oauth_revoke = 'https://owner-api.teslamotors.com/oauth/revoke'
    token_file = expanduser("~")+'/.tesla_token'


    def __init__(self, config: Config):
        ''' authenticate and save access token'''
        self.config = config
        self.token = None

    def logoff():
        self.revoke_token()
        self.delete_saved_token()

    def connect(self):
        while True:
            try:
                if self.token is None:
                    self.load_token()

                if self.config.revoke:
                    self.logoff()
                    exit(2)
                        
                if not self.is_token_valid():
                     self.get_token()
                     self.save_token()

                break

            except UnauthorizedException as uex:
                print("[!] Unauthorized. Please run again to re-login")
                self.logoff()
                self.get_token()
                self.save_token()


    def __del__(self):
        pass

    def revoke_token(self):
        ''' revoke access token to avoid pollution'''
        if self.token:
            response = post(Tesla.oauth_revoke, data='token={}'.format(self.token))
            print('[!] Token {} revoked with status code {}.'.format(self.token[:5], response.status_code))
            self.token=None
            self.delete_saved_token()

    def is_token_valid(self):
        return self.token is not None

    def load_token(self):
        try:
            with open(Tesla.token_file, 'r') as f:
                token_json = load(f)
                self.token = token_json['token']
        except:
            self.token = None 

    def save_token(self):
        with open(Tesla.token_file, 'w+') as f:
            dump({ 'token': self.token }, f)

    def delete_saved_token(self):
        try:
            remove(Tesla.token_file) 
        except:
            pass

    def get_token(self):
        self.config.get_credentials()

        response = post(Tesla.oauth_token, data = {
            'client_id': Tesla.client_id,
            'client_secret': Tesla.client_secret,
            'grant_type': 'password',
            'email': self.config.login,
            'password': self.config.password,
            })

        if (self.config.debug): print('Received {} {} response.'.format(response.status_code, response.reason))
        
        if response.status_code == 401:
            raise InvalidCredentialsException()
     
        if response.status_code > 299: 
            raise Exception('Invalid response: {} {}'.format(response.status_code, response.reason))

        payload = response.json()
        self.token = payload['access_token']

        print('[!] Received token: ...{}.'.format(self.token[:5]))

    def get_json(self,method: str):
        ''' execute an authenticated GET request against a given method'''
        headers = default_headers()
        headers.update({'Authorization': 'bearer {}'.format(self.token)}) 
    
        response = get(self.root.format(method),headers=headers)
        if self.config.debug: print(response.status_code, response.reason)
        
        if response.status_code == 408:
            raise VehicleAsleepException()
     
        if response.status_code == 401: 
            raise UnauthorizedException(response.reason)

        if response.status_code > 299: 
            raise UnexpectedResponseException('Invalid response: {} {}'.format(response.status_code, response.reason))

        json = response.json()

        if (self.config.debug): print(dumps(json, sort_keys=True, indent=4, separators=(',', ': ')))
    
        return json
    
    def post_json(self,method:str,json_data: dict = None):
        ''' execute an authenticated POST request against a given method, post provided data'''
        headers = default_headers()
        headers.update({'Authorization': 'bearer {}'.format(self.token)}) 
    
        response = post(self.root.format(method),data=json_data,headers=headers)
        json = response.json()
        if (self.config.debug): print(dumps(json, sort_keys=True, indent=4, separators=(',', ': ')))
        
        if response.status_code == 408:
            raise VehicleAsleepException()
        
        if response.status_code == 401: 
            raise UnauthorizedException(response.reason)
     
        if response.status_code > 299: 
            raise Exception('Invalid response: {} {}'.format(response.status_code, response.reason))

        if 'response' in json:
            if 'result' in json['response']:
                print('[*] Result: {}; reason: {}'.format(json['response']['result'], json['response']['reason']))

        return json

class Tesla(TeslaBase):
    def __init__(self,config):
        super().__init__(config)
        self.vehicle_id = None
        self.data = None
        

    def connect(self):
        super().connect()
        self.vehicle_id = self.get_json('/vehicles')['response'][0]['id']  


    def set_charge_limit(self, limit):
        self.post_json('/vehicles/{}/command/set_charge_limit'.format(self.vehicle_id), json_data={ 'percent': limit })

    def wake_up(self):
        while True:
            json = self.post_json('/vehicles/{}/wake_up'.format(self.vehicle_id))
            if 'response' in json:
                if 'state' in json['response']:
                    state = json['response']['state']
                    print('[*] Vehicle is {}'.format(state))
                    if state == 'online':
                        break
            sleep(10)
        


    def pull_data(self):
        self.data=self.get_json('/vehicles/{}/data'.format(self.vehicle_id))
        return self.data


    def print_stats(self):
        firmware_version = self.data['response']['vehicle_state']['car_version']
        print('    Current firmware version: {}'.format(firmware_version))
        
        update = self.data['response']['vehicle_state']['software_update']
        duration = update['expected_duration_sec']
        status = update['status']
        if status:
            print('[!] Software update: {}; Expected installation duration: {}'.format(status, duration))

        charge = self.data['response']['charge_state']

        battery_range = charge['battery_range']
        est_range = charge['est_battery_range']
        battery_level = charge['battery_level']
        
        print('    Battery:\n\tRange: \t\t\t{:0.0f} mi\n\tEstimated range: \t{:0.0f} mi\n\tBattery: \t\t{:0.0f} %\n\tTheoretical max range: \t{:0.0f} mi'.format(
            battery_range, 
            est_range,
            battery_level, 
            battery_range*100//battery_level,
            )
        )
            
        charge_limit = charge['charge_limit_soc']
        charge_state = charge['charging_state']

        print('    Current charge limit: \t{}%'.format(charge_limit))

        if charge_state == 'Charging' or charge_state == 'Complete':
            charge_rate = charge['charge_rate']
        
            wh_added = charge['charge_energy_added']
            mi_added = charge['charge_miles_added_ideal']

            current = charge['charger_actual_current']
            voltage = charge['charger_voltage']

            # todo: charge_current_request and calc charge deficit
            # todo: compare voltage and calculate power loss in the conductor

            time_to_full_charge = int(charge['time_to_full_charge']*60)
        
            print('    Charge:\n\tStarted at: \t\t{:0.0f} miles\n\tCurrent: \t\t{} Amp\n\tVoltage: \t\t{} V\n\tRate of \t\t{} mph\n\tTime to full charge: \t{} min'.format(
                battery_range-mi_added, 
                current, voltage, 
                charge_rate,
                time_to_full_charge))

            print('\tEngergy added: \t\t{} kwh ({:0.0f} miles).\n\tEstimated price: \t${:0.2f} at {} per kwh'.format(wh_added, mi_added, wh_added*self.config.rate, self.config.rate))
    
    def dump(self, filename: str):
        with open(filename, 'w') as outfile:
            dump(self.data, outfile, sort_keys=True, indent=4, separators=(',', ': '))

    def get_semver(self):
        (semver,_) = self.data['response']['vehicle_state']['car_version'].split(' ')
        return semver

    def get_charge_limit(self):
        return self.data['response']['charge_state']['charge_limit_soc']


    def charge_start(self):
        self.post_json('/vehicles/{}/command/charge_start'.format(self.vehicle_id))

    def charge_stop(self):
        self.post_json('/vehicles/{}/command/charge_start'.format(self.vehicle_id))

        
def main():
    config = Config()
    tesla = Tesla(config)
    
    try:
        tesla.connect()

        print('\n[*] Working with vehicle_id={}\n'.format(tesla.vehicle_id))

        if config.wakeup:
            tesla.wake_up()
                    
        tesla.pull_data()

        tesla.print_stats()

        if config.limit>0:
            print('    Updating the limit: {}%->{}%'.format(tesla.get_charge_limit(), config.limit))
            tesla.set_charge_limit(config.limit)
            tesla.pull_data()
            print('\tVerifying new limit: {} %'.format(tesla.get_charge_limit()))

        if config.charge_cmd=='start':
            print('[*] Starting charge')
            tesla.charge_start()

        if config.charge_cmd=='stop':
            print('[*] Stopping charge')
            tesla.charge_stop()

        if config.dump:
            filename = tesla.get_semver() + '.json'
            print('    Dumping config into {}'.format(filename))
            tesla.dump(filename)
            
    except InvalidCredentialsException as ex:
        print("[E] Invalid credentials: {}".format(ex))
    except VehicleAsleepException as ex:
        print("[!] Vehicle is asleep. Try walking it up with -w")
    except UnexpectedResponseException as ex:
        print("[E] Unexpected response: {}".format(ex))           
    except ConnectionError as err:
        print("[E] Connection error: {}".format(err))
        

main()
